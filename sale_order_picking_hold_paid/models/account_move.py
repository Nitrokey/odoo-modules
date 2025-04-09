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

    def _check_sale_order_pickings(self):
        """Create pickings for sale orders if they are now fully paid."""
        # Get all related sale orders from invoice lines
        orders = self.mapped("invoice_line_ids.sale_line_ids.order_id")

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
            if all(
                inv.payment_state == "paid"
                for inv in order.invoice_ids.filtered(lambda i: i.state == "posted")
            ):
                fully_paid += order

        # Create pickings for fully paid orders
        if fully_paid:
            fully_paid.create_pickings_if_paid()
