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

    def create_pickings_if_paid(self):
        """Create pickings for orders that are now fully paid."""
        # This method is called from account_move when invoices are paid
        # We don't need to check _is_fully_paid here because that's already done in account_move

        # Create pickings directly without using _create_picking
        # This bypasses the check in _create_picking for picking_hold_until_paid
        for order in self:
            if not order.picking_ids:
                # Create a picking for each order
                picking_vals = order._prepare_picking()
                picking = self.env["stock.picking"].create(picking_vals)

                # Create stock moves for each order line
                for line in order.order_line:
                    if line.product_id.type in ["product", "consu"]:
                        move_vals = line._prepare_stock_moves(picking)
                        for val in move_vals:
                            self.env["stock.move"].create(val)

                # Confirm the picking
                picking.action_confirm()
                picking.action_assign()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """Do not create stock moves if order is on hold and not for manufacturing."""
        # Filter out lines from orders that are on hold
        lines_to_process = self.filtered(
            lambda line: not line.order_id.picking_hold_until_paid
        )

        # For manufacturing orders, we need to process all lines
        mto_route = self.env.ref("stock.route_warehouse0_mto", raise_if_not_found=False)
        manufacture_route = self.env.ref(
            "mrp.route_warehouse0_manufacture", raise_if_not_found=False
        )

        if mto_route and manufacture_route:
            # Add lines that have MTO + Manufacturing routes even if order is on hold
            for line in self - lines_to_process:
                product_routes = line.product_id.route_ids
                if (
                    mto_route.id in product_routes.ids
                    and manufacture_route.id in product_routes.ids
                ):
                    lines_to_process |= line

        return super(SaleOrderLine, lines_to_process)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty
        )
