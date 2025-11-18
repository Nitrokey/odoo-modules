# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import TestCommon, TestInvoiceSendOnReconcileMixin


@tagged("post_install", "-at_install")
class TestInvoiceSendOnReconcile(TestCommon, TestInvoiceSendOnReconcileMixin):
    """Test automatic invoice sending on bank statement reconciliation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disable auto_delete on mail templates to allow testing
        cls.templates = cls.env["mail.template"].search([("auto_delete", "=", True)])
        cls.templates.write({"auto_delete": False})

        # Create test data
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "email": "customer@example.com",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "list_price": 100.0,
                "type": "service",
            }
        )
        cls.bank_journal = cls.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        if not cls.bank_journal:
            cls.bank_journal = cls.env["account.journal"].create(
                {
                    "name": "Test Bank",
                    "code": "TBNK",
                    "type": "bank",
                }
            )

    def test_invoice_sent_on_bank_statement_reconciliation(self):
        """Test that invoice email is sent when reconciling from bank statement."""
        # Create and post invoice
        invoice = self.create_invoice(self.partner, self.product, amount=100.0)
        invoice.action_post()

        # Verify invoice not sent initially
        self.assertFalse(invoice.is_move_sent)
        initial_mail_count = self.get_sent_mail_count(invoice)

        # Create bank statement
        bank_statement = self.env["account.bank.statement"].create(
            {
                "name": "Test Statement",
                "journal_id": self.bank_journal.id,
                "balance_end_real": 100.0,
            }
        )

        # Create bank statement line
        statement_line = self.env["account.bank.statement.line"].create(
            {
                "statement_id": bank_statement.id,
                "payment_ref": "Test Payment",
                "partner_id": self.partner.id,
                "amount": 100.0,
                "date": invoice.date,
            }
        )

        # Post the bank statement so its move entries can be reconciled
        bank_statement.button_post()

        # Get the receivable line from invoice
        receivable_line = invoice.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type == "receivable"
        )

        # Reconcile statement line with invoice
        statement_line.reconcile(
            [
                {
                    "id": receivable_line.id,
                }
            ]
        )

        # Verify invoice is marked as sent
        self.assertTrue(invoice.is_move_sent)

        # Verify email was sent
        final_mail_count = self.get_sent_mail_count(invoice)
        self.assertGreater(
            final_mail_count,
            initial_mail_count,
            "Invoice email should be sent after bank statement reconciliation",
        )

    def test_invoice_not_sent_if_already_sent(self):
        """Test that no duplicate email is sent if invoice already marked as sent."""
        # Create and post invoice
        invoice = self.create_invoice(self.partner, self.product, amount=100.0)
        invoice.action_post()

        # Mark invoice as already sent
        invoice.write({"is_move_sent": True})

        initial_mail_count = self.get_sent_mail_count(invoice)

        # Create bank statement
        bank_statement = self.env["account.bank.statement"].create(
            {
                "name": "Test Statement",
                "journal_id": self.bank_journal.id,
                "balance_end_real": 100.0,
            }
        )

        # Create bank statement line
        statement_line = self.env["account.bank.statement.line"].create(
            {
                "statement_id": bank_statement.id,
                "payment_ref": "Test Payment",
                "partner_id": self.partner.id,
                "amount": 100.0,
                "date": invoice.date,
            }
        )

        # Post the bank statement
        bank_statement.button_post()

        # Get the receivable line from invoice
        receivable_line = invoice.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type == "receivable"
        )

        # Reconcile statement line with invoice
        statement_line.reconcile(
            [
                {
                    "id": receivable_line.id,
                }
            ]
        )

        # Verify no additional email was sent
        final_mail_count = self.get_sent_mail_count(invoice)
        self.assertEqual(
            final_mail_count,
            initial_mail_count,
            "No duplicate email should be sent for already-sent invoice",
        )

    @classmethod
    def tearDownClass(cls):
        """Re-enable auto_delete on mail templates after tests."""
        super().tearDownClass()
        cls.templates.write({"auto_delete": True})
