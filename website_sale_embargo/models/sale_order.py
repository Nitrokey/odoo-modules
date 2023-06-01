from odoo import _, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm(self):
        for order in self:
            country_id = order.partner_shipping_id.country_id

            for rec in order.mapped("order_line"):
                hs_code = rec.product_id.product_tmpl_id.hs_code_id
                if hs_code and hs_code.embargo and country_id == hs_code.country_id:
                    raise ValidationError(
                        _("Product %(product)s is not available in country %(country)s")
                        % {
                            "product": rec.product_id.name,
                            "country": hs_code.country_id.name,
                        }
                    )
        return super()._action_confirm()

    def check_for_product_embargo(self, country_id):
        for rec in self.mapped("order_line"):
            hs_code = rec.product_id.product_tmpl_id.hs_code_id
            if hs_code and hs_code.embargo and country_id == hs_code.country_id:
                raise ValidationError(
                    _("Product %(product)s is not available in country %(country)s")
                    % {
                        "product": rec.product_id.name,
                        "country": hs_code.country_id.name,
                    }
                )
