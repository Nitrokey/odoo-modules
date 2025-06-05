# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("payment_term_id")
    def _onchange_payment_term_id(self):
        """Set delivery block when payment term requires holding until paid."""
        res = super()._onchange_payment_term_id()
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
        return res

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
