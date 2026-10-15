import json
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from . import common


@tagged("post_install", "-at_install")
class TestReturnShipment(common.DhlCommon):
    def test_return_shipment_success(self):
        picking = self._make_picking(qty=2)
        picking.origin = "SO42"
        response = common.mock_response(
            200, {"shipmentNo": "RET1", "label": {"b64": common.b64(b"RETURN-PDF")}}
        )
        with patch(common.CARRIER_REQUEST, return_value=response) as request:
            picking.dhl_parcel_de_provider_return_shipment()

        self.assertTrue(picking.is_return_shipment)
        self.assertEqual(picking.carrier_tracking_ref, "RET1")
        attachment = self._attachments(picking)
        self.assertEqual(attachment.mapped("name"), ["DHL_Return_Label_RET1.pdf"])
        self.assertEqual(attachment.raw, b"RETURN-PDF")

        kwargs = request.call_args.kwargs
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(
            kwargs["url"],
            f"{common.API_URL}/parcel/de/shipping/returns/v1/orders"
            "?labelType=SHIPMENT_LABEL",
        )
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer tok")
        payload = json.loads(kwargs["data"])
        self.assertEqual(payload["receiverId"], "RCV1")
        self.assertEqual(payload["shipmentReference"], "SO42")
        self.assertEqual(payload["itemWeight"], {"uom": "kg", "value": 4.0})
        shipper = payload["shipper"]
        self.assertEqual(shipper["name1"], "Max Mustermann")
        self.assertEqual(shipper["addressStreet"], "Hauptstr. 1")
        # addressHouse falls back to street2
        self.assertEqual(shipper["addressHouse"], "Apt 2")
        self.assertEqual(shipper["postalCode"], "10115")
        self.assertEqual(shipper["city"], "Berlin")
        items = payload["customsDetails"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["itemDescription"], "Test Widget")
        self.assertEqual(items[0]["packagedQuantity"], 2.0)

    def test_return_shipment_missing_weight(self):
        picking = self._make_picking(qty=0)
        with (
            patch(common.CARRIER_REQUEST) as request,
            self.assertRaises(ValidationError) as cm,
        ):
            picking.dhl_parcel_de_provider_return_shipment()
        self.assertIn("Shipping weight is missing", str(cm.exception))
        request.assert_not_called()
        self.assertFalse(picking.is_return_shipment)

    def test_return_shipment_missing_address(self):
        partner = self._make_partner(city=False)
        picking = self._make_picking(partner=partner)
        with (
            patch(common.CARRIER_REQUEST) as request,
            self.assertRaises(ValidationError) as cm,
        ):
            picking.dhl_parcel_de_provider_return_shipment()
        self.assertIn("city", str(cm.exception))
        request.assert_not_called()

    def test_return_shipment_http_error(self):
        picking = self._make_picking()
        with (
            patch(
                common.CARRIER_REQUEST,
                return_value=common.mock_response(400, text="rejected"),
            ),
            self.assertRaises(ValidationError) as cm,
        ):
            picking.dhl_parcel_de_provider_return_shipment()
        self.assertIn("rejected", str(cm.exception))
        self.assertFalse(picking.is_return_shipment)
        self.assertFalse(picking.carrier_tracking_ref)

    def test_return_shipment_answer_without_shipment_number(self):
        picking = self._make_picking()
        with (
            patch(
                common.CARRIER_REQUEST,
                return_value=common.mock_response(200, {"title": "oops"}),
            ),
            self.assertRaises(ValidationError),
        ):
            picking.dhl_parcel_de_provider_return_shipment()
        self.assertFalse(picking.is_return_shipment)
