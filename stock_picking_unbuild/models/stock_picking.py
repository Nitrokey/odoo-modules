from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_display_unbuild = fields.Boolean(compute="_compute_display_unbuild", store=True)

    @api.depends("picking_type_id", "picking_type_id.code")
    def _compute_display_unbuild(self):
        for picking in self:
            if picking.picking_type_id.code == "incoming":
                picking.is_display_unbuild = True
            else:
                picking.is_display_unbuild = False

    def action_generate_unbuild_order(self):
        mo_id = self.env["mrp.production"].search(
            [("origin", "=", self.sale_id.name)], limit=1
        )
        quantity = self.move_ids_without_package[0].quantity_done
        lot = mo_id.finished_move_line_ids and mo_id.finished_move_line_ids[0].lot_id
        unbuild_vals = {
            "mo_id": mo_id.id,
            "product_id": mo_id.product_id.id,
            "product_qty": quantity,
            "product_uom_id": mo_id.product_uom_id.id,
            "bom_id": mo_id.bom_id.id,
            "location_id": self.location_dest_id.id,
            "location_dest_id": self.location_dest_id.id,
            "lot_id": lot and lot.id,
        }
        unbuild_order = self.env["mrp.unbuild"].create(unbuild_vals)
        return {
            "type": "ir.actions.act_window",
            "name": _("Unbuild Order"),
            "res_model": "mrp.unbuild",
            "view_type": "form",
            "view_mode": "tree,form",
            "domain": [("id", "=", unbuild_order.id)],
        }
