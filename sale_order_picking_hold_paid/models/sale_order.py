# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        """Set delivery block when creating quotation with payment term that has
        delivery block reason."""
        order = super().create(vals)
        if order.payment_term_id and order.payment_term_id.delivery_block_reason_id:
            block_reason = order.payment_term_id.get_delivery_block_reason()
            if block_reason:
                order.delivery_block_id = block_reason
        return order

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """Avoid unsetting delivery block reason if it's not set on partner."""
        block_reason_before_onchange = self.delivery_block_id
        res = super().onchange_partner_id()
        if block_reason_before_onchange and not self.delivery_block_id:
            if partner_block_reason := self.partner_id.default_delivery_block:
                self.delivery_block_id = partner_block_reason
            else:
                self.delivery_block_id = block_reason_before_onchange
        return res

    @api.onchange("payment_term_id")
    def _onchange_payment_term_id(self):
        """Set delivery block when payment term has a delivery block reason."""
        if self.payment_term_id and self.payment_term_id.delivery_block_reason_id:
            block_reason = self.payment_term_id.get_delivery_block_reason()
            if block_reason:
                self.delivery_block_id = block_reason
        elif self.payment_term_id and not self.payment_term_id.delivery_block_reason_id:
            # Remove delivery block if payment term doesn't have a delivery block reason
            if self.delivery_block_id and self.delivery_block_id.remove_on_payment:
                self.delivery_block_id = False

    def action_confirm(self):
        """Ensure delivery block is set if payment term requires it."""
        result = super().action_confirm()
        for order in self:
            if (
                order.payment_term_id
                and order.payment_term_id.delivery_block_reason_id
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
                # Get all routes for the product (including category routes)
                product_routes = (
                    line.product_id.route_ids | line.product_id.categ_id.route_ids
                )
                # Also check warehouse routes
                warehouse = line.order_id.warehouse_id
                if warehouse:
                    product_routes |= warehouse.route_ids

                # Check if product has both MTO and Manufacturing routes
                has_mto = mto_route in product_routes
                has_manufacture = manufacture_route in product_routes

                if has_mto and has_manufacture:
                    lines_to_process |= line

        return super(SaleOrderLine, lines_to_process)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty
        )
