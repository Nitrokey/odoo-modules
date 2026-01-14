from odoo import models
from odoo.tools.float_utils import float_compare


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    # Insurance is now calculated dynamically at shipping time
    # No need for stored fields or complex default_get logic


def action_put_in_pack(self):
    """
    Simplified package creation - insurance calculated dynamically during shipping.
    """
    picking_move_lines = self.picking_id.move_line_ids
    move_line_ids = picking_move_lines.filtered(
        lambda ml: float_compare(
            ml.quantity, 0.0, precision_rounding=ml.product_uom_id.rounding
        )
        > 0
        and not ml.result_package_id
    )
    if not move_line_ids:
        move_line_ids = picking_move_lines.filtered(
            lambda ml: float_compare(
                ml.product_uom_qty, 0.0, precision_rounding=ml.product_uom_id.rounding
            )
            > 0
            and float_compare(
                ml.quantity, 0.0, precision_rounding=ml.product_uom_id.rounding
            )
            == 0
        )

    delivery_package = self.picking_id._put_in_pack(move_line_ids)
    # write shipping weight and package type on 'stock_quant_package' if needed
    if self.delivery_package_type_id:
        delivery_package.package_type_id = self.delivery_package_type_id
    if self.shipping_weight:
        delivery_package.shipping_weight = self.shipping_weight


ChooseDeliveryPackage.action_put_in_pack = action_put_in_pack
