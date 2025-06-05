# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    hold_picking_until_paid = fields.Boolean(
        help="If checked, delivery orders will be held until the invoice is fully paid",
        default=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure delivery block reason exists for payment terms with
        hold_picking_until_paid."""
        terms = super().create(vals_list)
        for term in terms:
            if term.hold_picking_until_paid:
                term._ensure_delivery_block_reason()
        return terms

    def write(self, vals):
        """Ensure delivery block reason exists when hold_picking_until_paid is enabled."""
        result = super().write(vals)
        if vals.get("hold_picking_until_paid"):
            for term in self:
                term._ensure_delivery_block_reason()
        return result

    def _ensure_delivery_block_reason(self):
        """Ensure a delivery block reason exists for this payment term."""
        if not hasattr(self, "_delivery_block_reason_id"):
            # Look for existing delivery block reason for this payment term
            block_reason = self.env["sale.delivery.block.reason"].search(
                [("name", "=", f"Hold until paid - {self.name}")], limit=1
            )

            if not block_reason:
                # Create new delivery block reason
                block_reason = self.env["sale.delivery.block.reason"].create(
                    {
                        "name": f"Hold until paid - {self.name}",
                        "description": f"Automatically created for payment term: {self.name}",
                        "remove_on_payment": True,
                    }
                )

            self._delivery_block_reason_id = block_reason

        return self._delivery_block_reason_id

    def get_delivery_block_reason(self):
        """Get the delivery block reason for this payment term."""
        if self.hold_picking_until_paid:
            return self._ensure_delivery_block_reason()
        return False
