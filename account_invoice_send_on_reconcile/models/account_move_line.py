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
                aaa
                continue

            # Send invoice email with error handling
            try:
                _logger.info(
                    "Sending invoice email for %s after reconciliation",
                    invoice.name,
                )
                # Get default invoice email template
                template = self.env.ref(
                    "account.email_template_edi_invoice", raise_if_not_found=False
                )
                if template:
                    bbbb
                    # Send email using template
                    template.send_mail(invoice.id, force_send=True)

                    # Mark invoice as sent
                    invoice.write({"is_move_sent": True})

                    _logger.info("Successfully sent invoice email for %s", invoice.name)
                else:
                    cccc
                    _logger.warning(
                        "No email template found for invoice %s", invoice.name
                    )
            except Exception as e:
                dddd
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
