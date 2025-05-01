# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """Check if pickings should be created when invoice is posted."""
        result = super()._post(soft=soft)
        self._check_sale_order_pickings()
        return result

    def write(self, vals):
        """Check if pickings should be created when payment state changes."""
        result = super().write(vals)
        if "payment_state" in vals:
            self._check_sale_order_pickings()
        return result

    def action_invoice_paid(self):
        """Check if pickings should be created when invoice is paid directly."""
        result = super().action_invoice_paid()
        self._check_sale_order_pickings()
        return result

    def _check_sale_order_pickings(self):
        """Create pickings for sale orders if they are now fully paid."""
        # Try multiple approaches to find related sale orders
        orders = self.env["sale.order"]

        # 1. Try through invoice lines
        line_orders = self.mapped("invoice_line_ids.sale_line_ids.order_id")
        orders |= line_orders

        # 2. Try through invoice origin (often contains sale order name)
        for move in self.filtered(
            lambda m: m.move_type == "out_invoice" and m.state == "posted"
        ):
            if move.invoice_origin:
                origin_orders = self.env["sale.order"].search(
                    [("name", "=", move.invoice_origin)]
                )
                orders |= origin_orders

        # 3. Try through direct relationship in sale.order
        for move in self:
            related_orders = self.env["sale.order"].search(
                [("invoice_ids", "in", [move.id])]
            )
            orders |= related_orders

        # Only process orders with hold_picking_until_paid
        orders_to_check = orders.filtered(lambda o: o.picking_hold_until_paid)

        if not orders_to_check:
            return

        # Find orders that are fully invoiced
        fully_invoiced = orders_to_check.filtered(
            lambda o: o.invoice_status == "invoiced"
        )

        # From fully invoiced orders, find those where all invoices are paid
        fully_paid = self.env["sale.order"]
        for order in fully_invoiced:
            posted_invoices = order.invoice_ids.filtered(lambda i: i.state == "posted")

            if not posted_invoices:
                continue

            all_paid = all(inv.payment_state == "paid" for inv in posted_invoices)

            if all_paid:
                fully_paid += order

        # Remove delivery block for fully paid orders
        if fully_paid:
            fully_paid.action_remove_delivery_block()
