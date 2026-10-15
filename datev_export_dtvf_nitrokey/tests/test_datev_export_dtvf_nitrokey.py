import base64
import io
import zipfile
from types import SimpleNamespace

from odoo.tests import tagged

from odoo.addons.datev_export_dtvf.tests import test_datev_export_dtvf


@tagged("post_install", "-at_install")
class TestDatevExportDtvfNitrokey(test_datev_export_dtvf.TestDatevExportDtvf):
    def test_happy_flow(self):
        return super().test_happy_flow()

    def _create_move(self, move_type, **vals):
        journal_type = "purchase" if move_type.startswith("in_") else "sale"
        journal = self.env["account.journal"].search(
            [("type", "=", journal_type), ("company_id", "=", self.env.company.id)],
            limit=1,
        ) or self.env["account.journal"].create(
            {
                "name": f"Test {journal_type}",
                "type": journal_type,
                "code": f"T{journal_type[:2].upper()}",
            }
        )
        return self.env["account.move"].create(
            {"move_type": move_type, "journal_id": journal.id, **vals}
        )

    def _export_lines(self):
        self.wizard.action_generate()
        zip_buffer = io.BytesIO(base64.b64decode(self.wizard.file_data))
        with zipfile.ZipFile(zip_buffer) as zip_file:
            name = [
                f for f in zip_file.namelist() if f.startswith("EXTF_Buchungsstapel")
            ][0]
            with zip_file.open(name) as move_line_file:
                # skip the two header lines
                return [line.decode("utf8") for line in move_line_file.readlines()[2:]]

    def test_references_vendor_bill(self):
        """Vendor bills use the vendor reference as first reference"""
        bill = self._create_move("in_invoice", ref="VENDOR-REF-1")
        self.assertEqual(
            self.wizard._get_matching_references(bill, "BILL/1", "x"),
            ("VENDOR-REF-1", "BILL/1"),
        )
        refund = self._create_move("in_refund", ref="VENDOR-RFND-1")
        self.assertEqual(
            self.wizard._get_matching_references(refund, "BILL/2", "x"),
            ("VENDOR-RFND-1", "BILL/2"),
        )

    def test_references_customer_invoice(self):
        """Customer invoices use the sale order reference if there is one"""
        invoice = self._create_move("out_invoice", invoice_origin="SO042")
        self.assertEqual(
            self.wizard._get_matching_references(invoice, "INV/1", "x"),
            ("SO042", "INV/1"),
        )

    def test_references_customer_invoice_without_origin(self):
        """Customer invoices without a sale order use the defaults"""
        invoice = self._create_move("out_invoice")
        self.assertEqual(
            self.wizard._get_matching_references(invoice, "INV/1", "ref2"),
            ("INV/1", "ref2"),
        )

    def test_references_customer_refund(self):
        """Customer refunds use the sale order of the reversed invoice"""
        invoice = self._create_move("out_invoice", invoice_origin="SO043")
        refund = self._create_move(
            "out_refund", name="RINV/1", reversed_entry_id=invoice.id
        )
        self.assertEqual(
            self.wizard._get_matching_references(refund, "INV/1", "x"),
            ("SO043", "INV/1"),
        )

    def test_references_customer_refund_own_name(self):
        """Customer refunds without origin use their own name if it differs"""
        refund = self._create_move("out_refund", name="RINV/2")
        self.assertEqual(
            self.wizard._get_matching_references(refund, "INV/2", "ref2"),
            ("RINV/2", "INV/2"),
        )

    def test_references_customer_refund_same_name(self):
        """Customer refunds with ref1 equal to their name use the defaults"""
        refund = self._create_move("out_refund", name="RINV/3")
        self.assertEqual(
            self.wizard._get_matching_references(refund, "RINV/3", "ref2"),
            ("RINV/3", "ref2"),
        )

    def test_references_entry_without_reconciliation(self):
        """Entries which are not reconciled use the defaults"""
        entry = SimpleNamespace(
            move_type="entry", mapped=lambda path: self.env["account.move"]
        )
        self.assertEqual(
            self.wizard._get_matching_references(entry, "MISC/1", "ref2"),
            ("MISC/1", "ref2"),
        )
        self.assertEqual(
            self.wizard._get_matching_references(self.move, "MISC/1", "ref2"),
            ("MISC/1", "ref2"),
        )

    def test_references_entry_reconciled_invoice(self):
        """Entries use the reference of the single reconciled invoice"""
        invoice = self._create_move("out_invoice", invoice_origin="SO044")
        entry = SimpleNamespace(move_type="entry", mapped=lambda path: invoice)
        self.assertEqual(
            self.wizard._get_matching_references(entry, "PAY/1", "ref2"),
            ("SO044", "PAY/1"),
        )

    def test_references_entry_multiple_invoices(self):
        """Entries reconciled with several invoices use the defaults"""
        invoices = self._create_move(
            "out_invoice", invoice_origin="SO045"
        ) | self._create_move("out_invoice", invoice_origin="SO046")
        entry = SimpleNamespace(move_type="entry", mapped=lambda path: invoices)
        self.assertEqual(
            self.wizard._get_matching_references(entry, "PAY/2", "ref2"),
            ("PAY/2", "ref2"),
        )

    def test_references_entry_reconciled_refund(self):
        """Entries fall back to the single reconciled refund"""
        invoice = self._create_move("out_invoice", invoice_origin="SO047")
        refund = self._create_move(
            "out_refund", name="RINV/4", reversed_entry_id=invoice.id
        )
        entry = SimpleNamespace(move_type="entry", mapped=lambda path: refund)
        # reference of the reversed invoice
        self.assertEqual(
            self.wizard._get_matching_references(entry, "PAY/3", "ref2"),
            ("SO047", "PAY/3"),
        )

    def test_references_entry_reconciled_refund_without_reversal(self):
        """Refunds not reversing an invoice are used directly for entries"""
        refund = self._create_move("out_refund", name="RINV/5")
        entry = SimpleNamespace(move_type="entry", mapped=lambda path: refund)
        self.assertEqual(
            self.wizard._get_matching_references(entry, "PAY/4", "ref2"),
            ("RINV/5", "PAY/4"),
        )

    def test_references_entry_only_unrelated_moves(self):
        """Entries reconciled with neither invoices nor refunds use the defaults"""
        other = self._create_move("entry")
        entry = SimpleNamespace(move_type="entry", mapped=lambda path: other)
        self.assertEqual(
            self.wizard._get_matching_references(entry, "PAY/5", "ref2"),
            ("PAY/5", "ref2"),
        )

    def test_export_references_and_text(self):
        """The export contains the references and the partner in the text"""
        partner = self.env["res.partner"].create({"name": "Nitro Test Partner"})
        self.move.partner_id = partner
        self.move.line_ids.write({"name": "Line text"})
        self.move.action_post()
        lines = self._export_lines()
        self.assertTrue(lines)
        self.assertIn("Line text Nitro Test Partner", lines[0])
        self.assertIn(f'"{self.move.name}"', lines[0])

    def test_export_text_without_partner(self):
        """Without a partner on the move the booking text is unchanged"""
        self.move.partner_id = False
        self.move.line_ids.write({"name": "Line text"})
        self.move.action_post()
        lines = self._export_lines()
        self.assertTrue(lines)
        self.assertIn('"Line text"', lines[0])
