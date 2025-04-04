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
        for move in self.filtered(
            lambda m: m.move_type == "out_invoice" and m.state == "posted"
        ):
            sale_orders = self.env["sale.order"].search(
                [
                    ("invoice_ids", "in", move.ids),
                    ("picking_hold_until_paid", "=", True),
                ]
            )

            # Create pickings for orders that are now fully paid
            sale_orders.create_pickings_if_paid()
