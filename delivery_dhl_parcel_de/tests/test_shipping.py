import json
from unittest.mock import patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from . import common

SHIPPING_URL = f"{common.API_URL}/parcel/de/shipping/v2/orders"


def _item(number, status=200, label=None, customs_doc=None):
    if label is None:
        label = {"b64": common.b64(b"PDF-" + number.encode())}
    item = {"sstatus": {"status": status}, "shipmentNo": number, "label": label}
    if customs_doc:
        item["customsDoc"] = {"b64": common.b64(customs_doc)}
    return item


def _answer(*items, status_code=200):
    return {"status": {"statusCode": status_code}, "items": list(items)}


@tagged("post_install", "-at_install")
class TestSendShipping(common.DhlCommon):
    def _send(self, picking, response):
        with patch(common.CARRIER_REQUEST, return_value=response) as request:
            result = self.carrier.dhl_parcel_de_provider_send_shipping(picking)
        return result, request

    def test_send_shipping_pdf(self):
        picking = self._make_picking()
        response = common.mock_response(200, _answer(_item("123")))
        result, request = self._send(picking, response)

        self.assertEqual(result, [{"exact_price": 0.0, "tracking_number": "123"}])

        kwargs = request.call_args.kwargs
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], f"{SHIPPING_URL}?docFormat=PDF")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer tok")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        payload = json.loads(kwargs["data"])
        self.assertEqual(len(payload["shipments"]), 1)
        shipment = payload["shipments"][0]
        self.assertEqual(shipment["product"], "V01PAK")
        self.assertEqual(shipment["refNo"], picking.name)
        self.assertEqual(shipment["details"]["weight"], {"uom": "kg", "value": 2.0})

        attachment = self._attachments(picking)
        self.assertEqual(attachment.mapped("name"), ["Shipping-Label-123.pdf"])
        self.assertEqual(attachment.raw, b"PDF-123")

    def test_send_shipping_zpl(self):
        self.carrier.dhl_document_format = "ZPL2"
        picking = self._make_picking()
        item = _item("321", label={"zpl2": "^XA^XZ"})
        result, request = self._send(picking, common.mock_response(200, _answer(item)))
        self.assertEqual(result[0]["tracking_number"], "321")
        self.assertTrue(request.call_args.kwargs["url"].endswith("docFormat=ZPL2"))
        attachment = self._attachments(picking)
        self.assertEqual(attachment.mapped("name"), ["Shipping-Label-321.zpl"])
        self.assertEqual(attachment.raw, b"^XA^XZ")

    def test_send_shipping_multi_status_with_customs_doc(self):
        """Status 207 is accepted; customs documents are attached as well."""
        picking = self._make_picking()
        answer = _answer(
            _item("111", customs_doc=b"CUSTOMS"), _item("222"), status_code=207
        )
        result, _request = self._send(picking, common.mock_response(207, answer))
        self.assertEqual(result[0]["tracking_number"], "111,222")
        names = self._attachments(picking).mapped("name")
        self.assertCountEqual(
            names,
            [
                "Shipping-Label-111.pdf",
                "Shipping-Label-222.pdf",
                "CustomsDoc-111.pdf",
            ],
        )

    def test_send_shipping_posts_tracking_message(self):
        picking = self._make_picking()
        self._send(picking, common.mock_response(200, _answer(_item("777"))))
        bodies = picking.message_ids.mapped("body")
        self.assertTrue(any("777" in (body or "") for body in bodies))

    def test_send_shipping_item_error(self):
        """An item with status 400 aborts the shipment."""
        picking = self._make_picking()
        answer = _answer(_item("123", status=400), status_code=207)
        with self.assertRaises(ValidationError):
            self._send(picking, common.mock_response(207, answer))

    def test_send_shipping_global_error_status(self):
        picking = self._make_picking()
        answer = _answer(_item("123"), status_code=500)
        with self.assertRaises(ValidationError):
            self._send(picking, common.mock_response(200, answer))

    def test_send_shipping_http_error(self):
        picking = self._make_picking()
        with self.assertRaises(ValidationError) as cm:
            self._send(picking, common.mock_response(401, text="Unauthorized!"))
        self.assertIn("Unauthorized!", str(cm.exception))
        self.assertFalse(self._attachments(picking))

    def test_send_shipping_connection_error(self):
        picking = self._make_picking()
        with (
            patch(common.CARRIER_REQUEST, side_effect=requests.Timeout("too slow")),
            self.assertRaises(ValidationError) as cm,
        ):
            self.carrier.dhl_parcel_de_provider_send_shipping(picking)
        self.assertIn("too slow", str(cm.exception))

    def test_send_shipping_missing_weight(self):
        picking = self._make_picking(qty=0)
        with (
            patch(common.CARRIER_REQUEST) as request,
            self.assertRaises(ValidationError) as cm,
        ):
            self.carrier.dhl_parcel_de_provider_send_shipping(picking)
        self.assertIn("Shipping weight is missing", str(cm.exception))
        request.assert_not_called()

    def test_send_shipping_missing_recipient_address(self):
        partner = self._make_partner(zip=False)
        picking = self._make_picking(partner=partner)
        with (
            patch(common.CARRIER_REQUEST) as request,
            self.assertRaises(ValidationError) as cm,
        ):
            self.carrier.dhl_parcel_de_provider_send_shipping(picking)
        self.assertIn("Recipient Address", str(cm.exception))
        self.assertNotIn("Shipper Address", str(cm.exception))
        request.assert_not_called()

    def test_send_shipping_missing_shipper_address(self):
        picking = self._make_picking()
        self.warehouse_partner.zip = False
        with (
            patch(common.CARRIER_REQUEST) as request,
            self.assertRaises(ValidationError) as cm,
        ):
            self.carrier.dhl_parcel_de_provider_send_shipping(picking)
        self.assertIn("Shipper Address", str(cm.exception))
        request.assert_not_called()

    def test_send_shipping_without_carrier_account(self):
        picking = self._make_picking()
        self.carrier.carrier_account_id = False
        with (
            patch(common.CARRIER_REQUEST) as request,
            self.assertRaises(ValidationError) as cm,
        ):
            self.carrier.dhl_parcel_de_provider_send_shipping(picking)
        self.assertIn("Carrier account is not set", str(cm.exception))
        request.assert_not_called()

    def test_send_shipping_via_core_dispatch(self):
        """``send_shipping`` dispatches to the DHL implementation."""
        picking = self._make_picking()
        with patch(
            common.CARRIER_REQUEST,
            return_value=common.mock_response(200, _answer(_item("555"))),
        ):
            result = self.carrier.send_shipping(picking)
        self.assertEqual(result[0]["tracking_number"], "555")


@tagged("post_install", "-at_install")
class TestCancelShipment(common.DhlCommon):
    def test_cancel_shipment_request(self):
        picking = self._make_picking()
        picking.carrier_tracking_ref = "111,222"
        response = common.mock_response(200, {"status": "ok"})
        with patch(common.CARRIER_REQUEST, return_value=response) as request:
            self.carrier.dhl_parcel_de_provider_cancel_shipment(picking)
        kwargs = request.call_args.kwargs
        self.assertEqual(kwargs["method"], "DELETE")
        self.assertEqual(
            kwargs["url"],
            f"{SHIPPING_URL}?profile=STANDARD_GRUPPENPROFIL"
            "&shipment=111&shipment=222",
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer tok")

    def test_cancel_shipment_via_picking(self):
        """The picking action clears the tracking reference afterwards."""
        picking = self._make_picking()
        picking.carrier_tracking_ref = "333"
        response = common.mock_response(200, {"status": "ok"})
        with patch(common.CARRIER_REQUEST, return_value=response) as request:
            picking.cancel_shipment()
        self.assertIn("shipment=333", request.call_args.kwargs["url"])
        self.assertFalse(picking.carrier_tracking_ref)

    def test_cancel_shipment_http_error(self):
        picking = self._make_picking()
        picking.carrier_tracking_ref = "444"
        with (
            patch(
                common.CARRIER_REQUEST,
                return_value=common.mock_response(404, text="unknown shipment"),
            ),
            self.assertRaises(ValidationError) as cm,
        ):
            self.carrier.dhl_parcel_de_provider_cancel_shipment(picking)
        # the error text of DHL must not get lost
        self.assertIn("unknown shipment", str(cm.exception))
