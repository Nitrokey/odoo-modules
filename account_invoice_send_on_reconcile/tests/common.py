# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestCommon(TransactionCase):
    """Base test class with tracking disabled."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))


class TestInvoiceSendOnReconcileMixin:
    """Mixin with helper methods for invoice send on reconcile tests."""

    def create_partner(self, name="Test Partner", email="test@example.com"):
        """Create a test partner with email."""
        return self.env["res.partner"].create(
            {
                "name": name,
                "email": email,
            }
        )

    def create_product(self, name="Test Product", price=100.0):
        """Create a test product."""
        return self.env["product.product"].create(
            {
                "name": name,
                "list_price": price,
                "type": "service",
            }
        )

    def create_invoice(self, partner, product, amount=100.0, move_type="out_invoice"):
        """Create a customer invoice.

        Args:
            partner: res.partner record
            product: product.product record
            amount: invoice amount
            move_type: 'out_invoice', 'out_refund', 'in_invoice', etc.

        Returns:
            account.move record
        """
        invoice = self.env["account.move"].create(
            {
                "partner_id": partner.id,
                "move_type": move_type,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "name": product.name,
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )
        return invoice

    def create_bank_journal(self, name="Bank", code="BNK1"):
        """Create a bank journal for payments."""
        return self.env["account.journal"].create(
            {
                "name": name,
                "code": code,
                "type": "bank",
            }
        )

    def reconcile_invoice_with_payment(self, invoice, journal=None):
        """Reconcile invoice with a payment using account.payment.register wizard.

        Args:
            invoice: account.move record (must be posted)
            journal: account.journal record (
                optional,
                uses first bank journal if not provided
            )

        Returns:
            dict: Result from _reconcile_payments
        """
        if journal is None:
            journal = self.env["account.journal"].search(
                [("type", "=", "bank")], limit=1
            )
            if not journal:
                journal = self.create_bank_journal()

        # Create payment register wizard
        ctx = {
            "active_model": "account.move",
            "active_ids": invoice.ids,
        }

        payment_register = (
            self.env["account.payment.register"]
            .with_context(**ctx)
            .create(
                {
                    "journal_id": journal.id,
                }
            )
        )

        # Process the payment (this calls _reconcile_payments internally)
        result = payment_register.action_create_payments()

        return result

    def get_sent_mail_count(self, invoice):
        """Get count of sent mails for an invoice.

        Args:
            invoice: account.move record

        Returns:
            int: Number of mail.mail records for this invoice
        """
        return self.env["mail.mail"].search_count(
            [
                ("model", "=", "account.move"),
                ("res_id", "=", invoice.id),
            ]
        )

    def create_payment_acquirer(self, provider="paypal"):
        """Create a payment acquirer for testing online payments.

        Args:
            provider: Provider name (paypal, stripe, etc.)

        Returns:
            payment.acquirer record
        """
        vals = {
            "name": f"Test {provider.title()}",
            "provider": provider,
            "state": "test",
        }

        # Add provider-specific required fields
        if provider == "paypal":
            vals["paypal_email_account"] = "test@paypal.example.com"

        return self.env["payment.acquirer"].create(vals)
