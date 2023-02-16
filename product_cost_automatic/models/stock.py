from odoo import models


class Picking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        res = super()._action_done()
        if res:
            for purchase in self.mapped("purchase_id"):
                for line in purchase.order_line:
                    if line.product_id.is_automatically:
                        price = line.price_unit
                        if (
                            line.product_id.product_tmpl_id.uom_po_id
                            != line.product_uom
                        ):
                            default_uom = line.product_id.product_tmpl_id.uom_po_id
                            price = line.product_uom._compute_price(
                                line.price_unit, default_uom
                            )
                        line.product_id.write({"standard_price": price or 0.0})
        return res
