# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        """Check if delivery blocks should be removed when invoice is paid."""
        res = super()._invoice_paid_hook()
        orders = self.filtered(lambda move: move.is_invoice()).mapped(
            "invoice_line_ids.sale_line_ids.order_id"
        )
        orders.with_context(auto_removal_on_payment=True).action_remove_delivery_block()
        return res
