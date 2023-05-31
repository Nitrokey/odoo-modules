from odoo import models, _

from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm(self):
        for order in self:
            country_id = order.partner_id.country_id

            for rec in order.mapped("order_line"):
                hs_code = rec.product_id.product_tmpl_id.hs_code_id
                if hs_code and hs_code.embargo and country_id == hs_code.country_id:
                    raise ValidationError(
                        _(
                            "Product %s is not available in country %s",
                            rec.product_id.name,
                            hs_code.country_id.name,
                        )
                    )
        return super()._action_confirm()
