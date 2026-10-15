from odoo.exceptions import ValidationError
from odoo.tests import tagged

from . import common


@tagged("post_install", "-at_install")
class TestPackageInfo(common.DhlCommon):
    # dhl_parcel_de_provider_get_package_info

    def test_domestic_package_info(self):
        picking = self._make_picking()
        data = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)
        self.assertEqual(data["product"], "V01PAK")
        self.assertEqual(data["billingNumber"], "22222222220102")
        self.assertEqual(data["refNo"], picking.name)
        self.assertEqual(
            data["consignee"],
            {
                "name1": "Max Mustermann",
                "name2": "Apt 2",
                "addressStreet": "Hauptstr. 1",
                "postalCode": "10115",
                "city": "Berlin",
                "country": "DEU",
                "email": "max@example.com",
                "phone": "+49301234567",
            },
        )
        shipper = data["shipper"]
        self.assertEqual(shipper["name1"], self.warehouse_partner.name)
        self.assertEqual(shipper["addressStreet"], "Lagerweg 5")
        self.assertEqual(shipper["postalCode"], "23552")
        self.assertEqual(shipper["country"], "DEU")
        # domestic: neither customs data nor services
        self.assertNotIn("customs", data)
        self.assertNotIn("services", data)

    def test_empty_values_are_removed(self):
        partner = self._make_partner(street2=False, email=False, phone=False)
        picking = self._make_picking(partner=partner)
        consignee = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)[
            "consignee"
        ]
        for key in ("name2", "name3", "email", "phone"):
            self.assertNotIn(key, consignee)
        self.assertEqual(consignee["name1"], "Max Mustermann")

    def test_company_recipient(self):
        """With a company name: company is name1, person name2, street2 name3."""
        partner = self._make_partner(company_name="ACME GmbH")
        picking = self._make_picking(partner=partner)
        consignee = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)[
            "consignee"
        ]
        self.assertEqual(consignee["name1"], "ACME GmbH")
        self.assertEqual(consignee["name2"], "Max Mustermann")
        self.assertEqual(consignee["name3"], "Apt 2")
        self.assertEqual(consignee["addressStreet"], "Hauptstr. 1")

    def test_packstation_recipient(self):
        partner = self._make_partner(street2="Packstation: 123")
        picking = self._make_picking(partner=partner)
        consignee = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)[
            "consignee"
        ]
        self.assertEqual(consignee["name1"], "Max Mustermann")
        self.assertEqual(consignee["name2"], "Hauptstr. 1")
        self.assertEqual(consignee["addressStreet"], "Packstation")
        self.assertEqual(consignee["addressHouse"], "123")
        self.assertNotIn("name3", consignee)

    def test_postfiliale_recipient(self):
        partner = self._make_partner(street2="POSTFILIALE 456")
        picking = self._make_picking(partner=partner)
        consignee = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)[
            "consignee"
        ]
        self.assertEqual(consignee["addressStreet"], "Postfiliale")
        self.assertEqual(consignee["addressHouse"], "456")

    def test_incoming_picking_swaps_parties(self):
        picking = self._make_picking(qty=0, incoming=True)
        data = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)
        self.assertEqual(data["shipper"]["name1"], "Max Mustermann")
        self.assertEqual(data["consignee"]["name1"], self.warehouse_partner.name)
        self.assertEqual(data["consignee"]["postalCode"], "23552")

    def test_services(self):
        picking = self._make_picking()
        self.carrier.write(
            {"dhl_premium": True, "dhl_bulky_goods": True, "dhl_endorsement": "RETURN"}
        )
        data = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 150.5)
        self.assertEqual(
            data["services"],
            {
                "additionalInsurance": {
                    "currency": self.company.currency_id.name,
                    "value": 150.5,
                },
                "premium": True,
                "bulkyGoods": True,
                "endorsement": True,
            },
        )

    def test_minimal_insurance_is_one(self):
        picking = self._make_picking()
        data = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0.2)
        self.assertEqual(data["services"]["additionalInsurance"]["value"], 1.0)

    def test_international_recipient_has_customs_data(self):
        partner = self._make_partner(
            country_id=self.us.id, zip="10001", city="New York"
        )
        picking = self._make_picking(qty=2, partner=partner)
        data = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)
        self.assertEqual(data["consignee"]["country"], "USA")
        customs = data["customs"]
        self.assertEqual(customs["exportType"], "OTHER")
        self.assertEqual(customs["exportDescription"], "Goods")
        self.assertEqual(
            customs["postalCharges"],
            {"currency": self.company.currency_id.name, "value": 0.0},
        )
        self.assertEqual(len(customs["items"]), 1)
        self.assertEqual(customs["items"][0]["itemDescription"], "Test Widget")

    def test_outside_customs_territory_has_customs_data(self):
        """Even within Europe, states outside the customs territory need customs."""
        state = self.env["res.country.state"].create(
            {
                "name": "Heligoland test",
                "code": "HGX",
                "country_id": self.de.id,
                "outside_customs_territory": True,
            }
        )
        partner = self._make_partner(state_id=state.id)
        picking = self._make_picking(partner=partner)
        data = self.carrier.dhl_parcel_de_provider_get_package_info(picking, 0)
        self.assertIn("customs", data)

    # prepare_product_data_request

    def test_product_data_without_sale_order(self):
        picking = self._make_picking(qty=2)
        items = self.carrier.prepare_product_data_request(picking)
        self.assertEqual(
            items,
            [
                {
                    "itemDescription": "Test Widget",
                    "packagedQuantity": 2.0,
                    "itemValue": {
                        "currency": self.company.currency_id.name,
                        "value": 20.0,
                    },
                    "itemWeight": {"uom": "kg", "value": 2.0},
                }
            ],
        )

    def test_product_data_hs_code_and_origin(self):
        hs_code = self.env["hs.code"].create(
            {"local_code": "8507601000", "description": "Accumulators"}
        )
        self.product.write({"hs_code_id": hs_code.id, "origin_country_id": self.de.id})
        picking = self._make_picking()
        item = self.carrier.prepare_product_data_request(picking)[0]
        self.assertEqual(item["hsCode"], hs_code.hs_code)
        self.assertEqual(item["countryOfOrigin"], "DEU")

    def test_product_data_gram_weight_is_integer(self):
        self.carrier.dhl_weight_uom = "g"
        self.product.weight = 2.7
        picking = self._make_picking()
        item = self.carrier.prepare_product_data_request(picking)[0]
        self.assertEqual(item["itemWeight"], {"uom": "g", "value": 2})
        self.assertIsInstance(item["itemWeight"]["value"], int)

    def test_product_data_from_sale_order_line(self):
        """With a sale order, the item value is the net unit price of the line."""
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "price_unit": 50.0,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        picking = order.picking_ids
        self.assertTrue(picking)
        picking.move_ids.quantity = 2
        item = self.carrier.prepare_product_data_request(picking)[0]
        self.assertEqual(item["itemValue"]["value"], 50.0)
        self.assertEqual(item["packagedQuantity"], 2.0)

    # dhl_parcel_de_provider_packages

    def test_packages_for_bulk_picking(self):
        picking = self._make_picking()
        packages = self.carrier.dhl_parcel_de_provider_packages(picking)
        self.assertEqual(len(packages), 1)
        details = packages[0]["details"]
        self.assertEqual(details["weight"], {"uom": "kg", "value": 2.0})
        self.assertEqual(details["dim"]["uom"], "mm")
        self.assertEqual(details["dim"]["length"], 300)
        self.assertEqual(details["dim"]["width"], 200)
        self.assertEqual(details["dim"]["height"], 100)
        # shipment data is merged into the package dict
        self.assertEqual(packages[0]["product"], "V01PAK")
        self.assertIn("consignee", packages[0])
        self.assertNotIn("services", packages[0])

    def test_packages_overweight(self):
        self.package_type.max_weight = 1.0
        picking = self._make_picking()
        with self.assertRaises(ValidationError):
            self.carrier.dhl_parcel_de_provider_packages(picking)
