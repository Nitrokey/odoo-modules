# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _run_manufacture(self, procurements):
        """Allow manufacturing orders to be created even if delivery is blocked.

        This ensures that manufacturing orders are created for products with
        Make-to-order and Manufacturing routes even if the delivery is
        blocked due to payment terms.
        """
        # Manufacturing orders should be created regardless of payment status
        # The filtering is already handled in the
        # sale_order_line._action_launch_stock_rule method
        return super()._run_manufacture(procurements)


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, procurements):
        """Override to ensure manufacturing orders are created."""
        # Extract procurements for manufacturing
        mfg_procurements = []
        other_procurements = []

        # Get manufacturing route
        manufacture_route = self.env.ref(
            "mrp.route_warehouse0_manufacture", raise_if_not_found=False
        )

        for procurement in procurements:
            product = procurement.product_id
            product_routes = product.route_ids + product.categ_id.route_ids

            if manufacture_route and manufacture_route.id in product_routes.ids:
                mfg_procurements.append(procurement)
            else:
                other_procurements.append(procurement)

        # Process manufacturing procurements first
        if mfg_procurements:
            super().run(mfg_procurements)

        # Process other procurements
        if other_procurements:
            super().run(other_procurements)

        return True
