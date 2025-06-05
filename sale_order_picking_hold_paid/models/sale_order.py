# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("payment_term_id")
    def _onchange_payment_term_id(self):
        """Set delivery block when payment term requires holding until paid."""
        if self.payment_term_id and self.payment_term_id.hold_picking_until_paid:
            block_reason = self.payment_term_id.get_delivery_block_reason()
            if block_reason:
                self.delivery_block_id = block_reason
        elif self.payment_term_id and not self.payment_term_id.hold_picking_until_paid:
            # Remove delivery block if payment term doesn't require holding
            if (
                self.delivery_block_id
                and self.delivery_block_id.remove_on_payment
                and "Hold until paid" in self.delivery_block_id.name
            ):
                self.delivery_block_id = False

    def action_confirm(self):
        """Ensure delivery block is set if payment term requires it."""
        result = super().action_confirm()
        for order in self:
            if (
                order.payment_term_id
                and order.payment_term_id.hold_picking_until_paid
                and not order.delivery_block_id
            ):
                block_reason = order.payment_term_id.get_delivery_block_reason()
                if block_reason:
                    order.delivery_block_id = block_reason
        return result

    def action_remove_delivery_block(self):
        """Remove the delivery block and create procurements as usual."""
        records = self
        if self.env.context.get("auto_removal_on_payment"):
            records = records.filtered("delivery_block_id.remove_on_payment")
        return super(SaleOrder, records).action_remove_delivery_block()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """Allow manufacturing orders even when delivery is blocked."""
        # Check if this line has manufacturing route
        mto_route = self.env.ref("stock.route_warehouse0_mto", raise_if_not_found=False)
        manufacture_route = self.env.ref(
            "mrp.route_warehouse0_manufacture", raise_if_not_found=False
        )

        lines_to_process = self.env["sale.order.line"]

        for line in self:
            # Allow if no delivery block
            if not line.order_id.delivery_block_id:
                lines_to_process |= line
            # Allow manufacturing lines even with delivery block
            elif mto_route and manufacture_route:
                product_routes = (
                    line.product_id.route_ids + line.product_id.categ_id.route_ids
                )
                if (
                    mto_route.id in product_routes.ids
                    and manufacture_route.id in product_routes.ids
                ):
                    lines_to_process |= line

        return super(SaleOrderLine, lines_to_process)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty
        )
