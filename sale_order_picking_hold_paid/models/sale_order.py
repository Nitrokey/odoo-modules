# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    picking_hold_until_paid = fields.Boolean(
        string="Hold Picking Until Paid",
        compute="_compute_picking_hold_until_paid",
        store=True,
        help="Technical field to indicate if picking should be held until invoice is paid",
    )

    @api.depends("payment_term_id", "payment_term_id.hold_picking_until_paid")
    def _compute_picking_hold_until_paid(self):
        """Compute if picking should be held based on payment term setting."""
        for order in self:
            order.picking_hold_until_paid = (
                order.payment_term_id.hold_picking_until_paid
                if order.payment_term_id
                else False
            )

    def _create_picking(self):
        """Override to prevent picking creation if hold_picking_until_paid is enabled."""
        # Only create pickings for orders that don't need to be held or are fully paid
        orders_to_process = self.env["sale.order"]
        for order in self:
            if not order.picking_hold_until_paid or order._is_fully_paid():
                orders_to_process += order
        return super(SaleOrder, orders_to_process)._create_picking()

    def _is_fully_paid(self):
        """Check if the order is fully invoiced and all invoices are paid."""
        self.ensure_one()

        # Check if the order is fully invoiced or nothing to invoice
        if self.invoice_status not in ["invoiced", "no"]:
            return False

        # If there are no invoices but nothing to invoice, consider it paid
        if not self.invoice_ids and self.invoice_status == "no":
            return True

        # Check if all posted invoices are paid
        posted_invoices = self.invoice_ids.filtered(lambda i: i.state == "posted")
        if not posted_invoices:
            return False

        return all(inv.payment_state == "paid" for inv in posted_invoices)

    def action_remove_delivery_block(self):
        """Remove the delivery block and create procurements as usual."""
        for order in self:
            if not order.picking_ids:
                # Temporarily set picking_hold_until_paid to False
                order.write({"picking_hold_until_paid": False})
                
                # If the order has a delivery_block_id (from sale_stock_picking_blocking),
                # we need to handle that as well
                had_block = False
                if hasattr(order, 'delivery_block_id') and order.delivery_block_id:
                    had_block = True
                    # Store the original delivery_block_id
                    original_block = order.delivery_block_id
                    # Remove the delivery block
                    order.write({"delivery_block_id": False})
                
                # Create the picking using the standard method
                order.order_line._action_launch_stock_rule()
                
                # Restore the picking_hold_until_paid flag
                order.write({"picking_hold_until_paid": True})
                
                # Restore the delivery_block_id if it was set
                if had_block:
                    order.write({"delivery_block_id": original_block.id})
        return True


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """Do not create stock moves if order is on hold and not for manufacturing."""
        # Filter out lines from orders that are on hold
        lines_to_process = self.filtered(
            lambda line: not line.order_id.picking_hold_until_paid and 
                        (not hasattr(line.order_id, 'delivery_block_id') or 
                         not line.order_id.delivery_block_id)
        )

        # For manufacturing orders, we need to process all lines
        mto_route = self.env.ref("stock.route_warehouse0_mto", raise_if_not_found=False)
        manufacture_route = self.env.ref(
            "mrp.route_warehouse0_manufacture", raise_if_not_found=False
        )

        if mto_route and manufacture_route:
            # Add lines that have MTO + Manufacturing routes even if order is on hold
            for line in self - lines_to_process:
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
