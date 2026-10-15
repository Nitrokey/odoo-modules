from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.product.models.product_template import ProductTemplate

from . import common


@tagged("post_install", "-at_install")
class TestCarrierHelpers(common.DhlCommon):
    # convert_weight

    def _convert(self, odoo_uom, dhl_uom, value):
        self.carrier.dhl_weight_uom = dhl_uom
        with patch.object(
            ProductTemplate,
            "_get_weight_uom_id_from_ir_config_parameter",
            return_value=SimpleNamespace(name=odoo_uom),
        ):
            return self.carrier.convert_weight(value)

    def test_convert_weight_same_unit(self):
        self.assertEqual(self._convert("kg", "kg", 1.234), 1.234)
        self.assertEqual(self._convert("g", "g", 1234), 1234)

    def test_convert_weight_kg_to_g(self):
        result = self._convert("kg", "g", 1.5)
        self.assertEqual(result, 1500)
        self.assertIsInstance(result, int)

    def test_convert_weight_g_to_kg(self):
        self.assertEqual(self._convert("g", "kg", 1500), 1.5)
        self.assertEqual(self._convert("g", "kg", 1234.5678), 1.235)

    def test_convert_weight_unsupported_unit(self):
        """Pounds are not supported: nothing is returned."""
        self.assertIsNone(self._convert("lb", "kg", 3.0))

    # check_address_details

    def test_check_address_details_complete(self):
        self.assertFalse(
            self.carrier.check_address_details(
                self.partner, ["zip", "city", "country_id", "street"]
            )
        )

    def test_check_address_details_missing(self):
        partner = self._make_partner(zip=False, country_id=False)
        message = self.carrier.check_address_details(
            partner, ["zip", "city", "country_id"]
        )
        self.assertIn("Missing Values For Address", message)
        self.assertIn("zip, country", message)
        self.assertNotIn("city", message)

    # insurance

    def test_calculate_package_insurance(self):
        picking = SimpleNamespace(declared_value=100.0)
        self.assertEqual(self.carrier._calculate_package_insurance(picking, 1, 4), 25)
        self.assertEqual(
            self.carrier._calculate_package_insurance(picking, 4, 4), 100.0
        )

    def test_calculate_package_insurance_zero(self):
        self.assertEqual(
            self.carrier._calculate_package_insurance(
                SimpleNamespace(declared_value=0.0), 1, 4
            ),
            0.0,
        )
        self.assertEqual(
            self.carrier._calculate_package_insurance(
                SimpleNamespace(declared_value=100.0), 1, 0
            ),
            0.0,
        )

    # package dict

    def test_create_package_dict_kg(self):
        self.assertEqual(
            self.carrier.create_dhl_de_package_dict(10, 30, 20, 1.5),
            {
                "details": {
                    "dim": {"uom": "mm", "height": 10, "length": 30, "width": 20},
                    "weight": {"uom": "kg", "value": 1.5},
                }
            },
        )

    def test_create_package_dict_gram_is_integer(self):
        self.carrier.dhl_weight_uom = "g"
        weight = self.carrier.create_dhl_de_package_dict(1, 2, 3, 1500.0)["details"][
            "weight"
        ]
        self.assertEqual(weight, {"uom": "g", "value": 1500})
        self.assertIsInstance(weight["value"], int)

    # verify packages

    def test_verify_packages_no_package_types(self):
        self.package_type.max_weight = 0
        with self.assertRaises(ValidationError) as cm:
            self.carrier._verify_dhl_parcel_packages([])
        self.assertIn("No package types configured", str(cm.exception))

    def test_verify_packages_overweight(self):
        package = SimpleNamespace(weight=10.5, packaging_type="TESTBOX")
        with self.assertRaises(ValidationError) as cm:
            self.carrier._verify_dhl_parcel_packages([package])
        self.assertIn("higher than the maximum", str(cm.exception))

    def test_verify_packages_ok(self):
        """Weight at the limit, or a package code we do not know, passes."""
        self.carrier._verify_dhl_parcel_packages(
            [
                SimpleNamespace(weight=10.0, packaging_type="TESTBOX"),
                SimpleNamespace(weight=999.0, packaging_type="UNKNOWN"),
                SimpleNamespace(weight=999.0, packaging_type=False),
            ]
        )

    # rate shipment

    def _make_order(self, partner=None, product=None):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "partner_shipping_id": (partner or self.partner).id,
                "warehouse_id": self.out_type.warehouse_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": (product or self.product).id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )

    def test_rate_shipment_success(self):
        result = self.carrier.dhl_parcel_de_provider_rate_shipment(self._make_order())
        self.assertEqual(
            result,
            {
                "success": True,
                "price": 0.0,
                "error_message": False,
                "warning_message": False,
            },
        )

    def test_rate_shipment_bad_recipient_address(self):
        partner = self._make_partner(city=False)
        result = self.carrier.dhl_parcel_de_provider_rate_shipment(
            self._make_order(partner)
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["price"], 0.0)
        self.assertIn("Recipient Address", result["error_message"])
        self.assertIn("city", result["error_message"])
        self.assertNotIn("Shipper Address", result["error_message"])

    def test_rate_shipment_bad_shipper_address(self):
        self.warehouse_partner.street = False
        result = self.carrier.dhl_parcel_de_provider_rate_shipment(self._make_order())
        self.assertFalse(result["success"])
        self.assertIn("Shipper Address", result["error_message"])
        self.assertNotIn("Recipient Address", result["error_message"])

    def test_rate_shipment_product_without_weight(self):
        light = self.env["product.product"].create(
            {"name": "Weightless", "type": "consu", "weight": 0.0}
        )
        result = self.carrier.dhl_parcel_de_provider_rate_shipment(
            self._make_order(product=light)
        )
        self.assertFalse(result["success"])
        self.assertIn(
            "product weight is not available : Weightless", result["error_message"]
        )

    # create shipment (HTTP layer)

    def test_create_shipment_success_codes(self):
        for code in (200, 201, 207):
            response = common.mock_response(code, {"ok": code})
            with patch(common.CARRIER_REQUEST, return_value=response) as request:
                status, data = self.carrier.dhl_parcel_de_provider_create_shipment(
                    "POST", "https://x", "{}", {"h": "v"}
                )
            self.assertTrue(status)
            self.assertEqual(data, {"ok": code})
            request.assert_called_once_with(
                method="POST",
                url="https://x",
                headers={"h": "v"},
                data="{}",
                timeout=30,
            )

    def test_create_shipment_error_returns_text(self):
        response = common.mock_response(400, text="bad request")
        with patch(common.CARRIER_REQUEST, return_value=response):
            status, data = self.carrier.dhl_parcel_de_provider_create_shipment(
                "POST", "https://x", "{}", {}
            )
        self.assertFalse(status)
        self.assertEqual(data, "bad request")

    # tracking link

    def test_tracking_link_uses_latest_number(self):
        self.carrier.dhl_tracking_url = "https://track.test/?c="
        picking = SimpleNamespace(carrier_tracking_ref="111,222")
        self.assertEqual(
            self.carrier.dhl_parcel_de_provider_get_tracking_link(picking),
            "https://track.test/?c=222",
        )

    def test_tracking_link_default_url(self):
        picking = SimpleNamespace(carrier_tracking_ref="999")
        link = self.carrier.dhl_parcel_de_provider_get_tracking_link(picking)
        self.assertTrue(link.endswith("piececode=999"))

    def test_tracking_link_without_url(self):
        self.carrier.dhl_tracking_url = False
        with self.assertRaises(ValidationError):
            self.carrier.dhl_parcel_de_provider_get_tracking_link(
                SimpleNamespace(carrier_tracking_ref="1")
            )
