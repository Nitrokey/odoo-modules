from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["bitcoin"] = {"mode": "unique", "domain": [("type", "=", "bank")]}
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for move in self:
            sale_order_id = move.invoice_line_ids.mapped("sale_line_ids")
            if sale_order_id:
                move.ref = sale_order_id.order_id.name
        return res
