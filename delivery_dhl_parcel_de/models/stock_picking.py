import binascii
import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_return_shipment = fields.Boolean(copy=False)
    picking_type_code = fields.Selection(
        related="picking_type_id.code",
        store=True,
        readonly=True,
    )
    declared_value_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Declared Value Currency",
        compute="_compute_declared_value_currency_id",
        store=True,
        readonly=True,
    )
    declared_value = fields.Monetary(
        currency_field="declared_value_currency_id",
        compute="_compute_declared_value",
        store=True,
        readonly=False,
        help="Declared value for shipping insurance.",
    )

    @api.depends(
        "sale_id", "sale_id.currency_id", "company_id", "company_id.currency_id"
    )
    def _compute_declared_value_currency_id(self):
        for picking in self:
            if picking.sale_id and picking.sale_id.currency_id:
                picking.declared_value_currency_id = picking.sale_id.currency_id
            else:
                picking.declared_value_currency_id = picking.company_id.currency_id

    def _get_declared_value_base_amount(self):
        self.ensure_one()
        if not self.sale_id:
            return 0.0
        total = 0.0
        for move in self.move_ids:
            sale_line = move.sale_line_id
            if not sale_line or not sale_line.product_uom_qty:
                continue
            unit_price = sale_line.price_total / sale_line.product_uom_qty
            total += unit_price * move.quantity
        return total

    @api.depends(
        "sale_id",
        "move_ids.quantity",
        "move_ids.sale_line_id.price_total",
        "move_ids.sale_line_id.product_uom_qty",
        "carrier_id",
    )
    def _compute_declared_value(self):
        for picking in self:
            picking.declared_value = picking._get_declared_value_base_amount() * (
                picking.carrier_id.declared_value_percentage / 100.0
            )

    def dhl_parcel_de_provider_return_shipment(self):
        """
        This method is used to return shipment of DHL Parcel.
        @return: Return Label & Tracking Number
        """
        try:
            carrier_id = self.carrier_id
            carrier_account_id = carrier_id.carrier_account_id
            shipper_address_error = carrier_id.check_address_details(
                self.partner_id, ["zip", "city", "street"]
            )
            if shipper_address_error or not self.shipping_weight:
                raise ValidationError(
                    ", ".join(
                        [
                            "Shipper Address : %s \n" % shipper_address_error  # noqa: UP031
                            if shipper_address_error
                            else "",
                            "Shipping weight is missing!"
                            if not self.shipping_weight
                            else "",
                        ]
                    )
                )
            products_data = carrier_id.prepare_product_data_request(self)
            request_data = json.dumps(
                {
                    "receiverId": carrier_id.dhl_return_receiver_id,
                    "shipmentReference": self.origin or "",
                    "shipper": {
                        "name1": self.partner_id.name or "",
                        "name2": self.partner_id.parent_id
                        and self.partner_id.parent_id.name
                        or "",
                        "addressStreet": self.partner_id.street or "",
                        "addressHouse": self.partner_id.street2
                        or self.partner_id.street
                        or "",
                        "city": self.partner_id.city or "",
                        "email": self.partner_id.email or "",
                        "phone": self.partner_id.phone or "",
                        "postalCode": self.partner_id.zip or "",
                        "state": self.partner_id.state_id
                        and self.partner_id.state_id.code
                        or "",
                    },
                    "itemWeight": {
                        "uom": carrier_id.dhl_weight_uom or "",
                        "value": self.shipping_weight,
                    },
                    "customsDetails": {"items": products_data},
                }
            )
            headers = {
                "content-type": "application/json",
                "Authorization": f"Bearer {carrier_account_id.dhl_access_token}",
            }
            api_url = f"{carrier_account_id.dhl_parcel_de_api_url}/parcel/de/shipping/returns/v1/orders?labelType=SHIPMENT_LABEL"  # noqa: E501
            request_type = "POST"
            response_status, response_data = (
                carrier_id.dhl_parcel_de_provider_create_shipment(
                    request_type, api_url, request_data, headers
                )
            )
            if response_status and response_data.get("shipmentNo"):
                return_track_number = response_data.get("shipmentNo")
                self.is_return_shipment = True
                self.carrier_tracking_ref = return_track_number
                label_data = response_data.get("label").get("b64")
                label_data = binascii.a2b_base64(label_data)
                message = "Return Shipping Number : %s" % return_track_number  # noqa:UP031
                self.message_post(
                    body=message,
                    attachments=[
                        ("DHL_Return_Label_%s.pdf" % return_track_number, label_data)  # noqa:UP031
                    ],
                )
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)  # noqa: B904
