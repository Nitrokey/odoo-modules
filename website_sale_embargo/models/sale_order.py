import logging

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm(self):
        for order in self:
            country_id = order.partner_shipping_id.country_id

            for rec in order.mapped("order_line"):
                hs_code = rec.product_id.product_tmpl_id.hs_code_id
                embargo_countries = [country.id for country in hs_code.country_id]
                if hs_code and embargo_countries and country_id.id in embargo_countries:
                    raise ValidationError(
                        _("Product %(product)s is not available in country %(country)s")
                        % {
                            "product": rec.product_id.name,
                            "country": country_id.name,
                        }
                    )
        return super()._action_confirm()

    def check_for_product_embargo(self, country_id, raise_validation=False):
        for rec in self.mapped("order_line"):
            hs_code = rec.product_id.product_tmpl_id.hs_code_id
            embargo_countries = [country.id for country in hs_code.country_id]
            if embargo_countries and country_id.id in embargo_countries:
                error_msg = _(
                    "Product %(product)s is not available in country %(country)s"
                ) % {
                    "product": rec.product_id.name,
                    "country": country_id.name,
                }
                if raise_validation:
                    raise ValidationError(error_msg)
                _logger.warning(error_msg)
                return error_msg
        return False
