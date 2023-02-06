import base64

from odoo import fields, models


class UPSReturnDeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def ups_send_shipping(self, pickings):
        res = super().ups_send_shipping(pickings)
        if res[0].get("attachments"):
            picking_vals = {
                "ups_image": base64.b64encode(res[0].get("attachments")[0][1])
            }
            pickings.write(picking_vals)

        return res[0]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ups_image = fields.Binary(string="UPS Image")
