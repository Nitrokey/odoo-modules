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
            order = move.invoice_line_ids.mapped("sale_line_ids.order_id")
            if order:
                move.ref = ", ".join(order.mapped("name"))
        return res
