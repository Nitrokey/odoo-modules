# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def reconcile(self):
        """Override to automatically send invoice emails after reconciliation.

        This method is called when move lines are reconciled, including
        bank statement reconciliation and payment register.
        """
        # Call parent method to perform standard reconciliation
        res = super().reconcile()

        # Get all invoices from the reconciled move lines
        invoices = self.mapped("move_id").filtered(
            lambda m: m.is_invoice(include_receipts=True)
        )

        for invoice in invoices:
            # Skip if not a valid invoice for sending
            if not self._should_send_invoice_after_reconciliation(invoice):
                continue

            # Send invoice email with error handling
            try:
                _logger.info(
                    "Sending invoice email for %s after reconciliation",
                    invoice.name,
                )

                # Get email context from action_invoice_sent
                action_dict = invoice.action_invoice_sent()
                if action_dict and action_dict.get("context"):
                    email_ctx = action_dict["context"]
                    invoice.with_context(**email_ctx).message_post_with_template(
                        email_ctx.get("default_template_id")
                    )

                # Mark invoice as sent
                invoice.write({"is_move_sent": True})

                _logger.info("Successfully sent invoice email for %s", invoice.name)
            except Exception as e:
                # Log error but don't break reconciliation process
                _logger.error(
                    "Failed to send invoice email for %s: %s",
                    invoice.name,
                    str(e),
                    exc_info=True,
                )

        return res

    def _should_send_invoice_after_reconciliation(self, invoice):
        """Determine if invoice should be sent after bank statement reconciliation.

        Checks multiple conditions:
        - Invoice must be posted
        - Must be customer invoice (out_invoice only)
        - Must be fully paid
        - Must not already be sent

        Args:
            invoice: account.move record

        Returns:
            bool: True if invoice should be sent, False otherwise
        """
        # Check basic invoice conditions
        if invoice.state != "posted":
            return False

        if invoice.move_type != "out_invoice":
            return False

        if invoice.payment_state != "paid":
            return False

        if invoice.is_move_sent:
            return False

        return True
