# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _run_manufacture(self, procurements):
        """Allow manufacturing orders to be created even if delivery is blocked.

        This ensures that manufacturing orders are created for products with
        Make-to-order and Manufacturing routes, even if the delivery is
        blocked due to payment terms.
        """
        # Manufacturing orders should be created regardless of payment status
        # The filtering is already handled in the
        # sale_order_line._action_launch_stock_rule method
        return super()._run_manufacture(procurements)
