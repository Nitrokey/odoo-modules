import logging

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def check_for_product_embargo(self, country_id, raise_error=False):
        for line in self.order_line:
            hs = line.product_id.product_tmpl_id.hs_code_id
            if hs and country_id.id in hs.country_id.ids:
                msg = _("Product %(p)s is not available in country %(c)s") % {
                    "p": line.product_id.display_name,
                    "c": country_id.name,
                }
                if raise_error:
                    raise ValidationError(msg)
                _logger.warning(msg)
                return msg
        return False

    def _action_confirm(self):
        for order in self:
            order.check_for_product_embargo(
                order.partner_shipping_id.country_id, raise_error=True
            )
        return super()._action_confirm()
