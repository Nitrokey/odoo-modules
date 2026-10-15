import base64
from unittest.mock import Mock

from odoo.tests.common import TransactionCase

MODELS = "odoo.addons.delivery_dhl_parcel_de.models"
CARRIER_REQUEST = f"{MODELS}.delivery_carrier.requests.request"
ACCOUNT_REQUEST = f"{MODELS}.carrier_account.requests.request"
API_URL = "https://dhl.test"


def mock_response(status_code=200, json_data=None, text=""):
    """Build a stand-in for a ``requests.Response``."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.text = text
    return response


def b64(data):
    return base64.b64encode(data).decode()


class DhlCommon(TransactionCase):
    """Shared fixtures: DHL carrier, account, package type, partners, pickings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.de = env.ref("base.de")
        cls.us = env.ref("base.us")
        cls.company = env.company

        # Disable pre-existing DHL package types so that only ours are checked
        env["stock.package.type"].search(
            [("package_carrier_type", "=", "dhl_parcel_de_provider")]
        ).write({"max_weight": 0})
        cls.package_type = env["stock.package.type"].create(
            {
                "name": "Test DHL box",
                "package_carrier_type": "dhl_parcel_de_provider",
                "packaging_length": 300,
                "width": 200,
                "height": 100,
                "max_weight": 10.0,
                "shipper_package_code": "TESTBOX",
            }
        )
        cls.account = env["carrier.account"].create(
            {
                "name": "DHL test account",
                "delivery_type": "dhl_parcel_de_provider",
                "account": "2222222222",
                "password": "secret",
                "dhl_parcel_de_api_url": API_URL,
                "dhl_userid": "user",
                "dhl_api_key": "key",
                "dhl_api_secret": "shh",
                "dhl_access_token": "tok",
            }
        )
        cls.carrier = env["delivery.carrier"].create(
            {
                "name": "DHL test",
                "delivery_type": "dhl_parcel_de_provider",
                "product_id": env.ref("delivery.product_product_delivery").id,
                "company_id": cls.company.id,
                "carrier_account_id": cls.account.id,
                "dhl_parcel_de_provider_package_id": cls.package_type.id,
                "dhl_weight_uom": "kg",
                "dhl_services_name": "V01PAK",
                "dhl_procedure_no": "01",
                "dhl_participation_no": "02",
                "dhl_document_format": "PDF",
                "dhl_export_type": "OTHER",
                "dhl_export_type_description": "Goods",
                "dhl_endorsement": False,
                "dhl_return_receiver_id": "RCV1",
            }
        )
        cls.out_type = env.ref("stock.picking_type_out")
        cls.in_type = env.ref("stock.picking_type_in")
        cls.warehouse_partner = cls.out_type.warehouse_id.partner_id
        cls.warehouse_partner.write(
            {
                "street": "Lagerweg 5",
                "zip": "23552",
                "city": "Luebeck",
                "country_id": cls.de.id,
            }
        )
        cls.partner = cls._make_partner()
        cls.product = env["product.product"].create(
            {"name": "Test Widget", "type": "consu", "weight": 2.0, "list_price": 10.0}
        )

    @classmethod
    def _make_partner(cls, **vals):
        values = {
            "name": "Max Mustermann",
            "street": "Hauptstr. 1",
            "street2": "Apt 2",
            "zip": "10115",
            "city": "Berlin",
            "country_id": cls.de.id,
            "email": "max@example.com",
            "phone": "+49301234567",
        }
        values.update(vals)
        return cls.env["res.partner"].create(values)

    def _make_picking(self, qty=1.0, partner=None, incoming=False):
        """Create a picking carrying ``qty`` units of the test product."""
        picking_type = self.in_type if incoming else self.out_type
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": (partner or self.partner).id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "carrier_id": self.carrier.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": qty,
                            "product_uom": self.product.uom_id.id,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": (
                                picking_type.default_location_dest_id.id
                            ),
                        },
                    )
                ]
                if qty
                else [],
            }
        )
        if qty:
            picking.action_confirm()
            picking.move_ids.quantity = qty
        return picking

    def _attachments(self, picking):
        return self.env["ir.attachment"].search(
            [("res_model", "=", "stock.picking"), ("res_id", "=", picking.id)]
        )
