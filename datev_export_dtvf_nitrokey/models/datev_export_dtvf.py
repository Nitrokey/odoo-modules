# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class DatevExportDtvfExport(models.Model):
    _inherit = "datev_export_dtvf.export"

    def _get_matching_references(self, move, ref1, ref2):
        # Incoming invoices will use the vendor reference
        if move.move_type.startswith("in_"):
            return move.ref, ref1

        # Outgoing invoices will use the sale.order reference
        if move.move_type == "out_invoice" and move.invoice_origin:
            return move.invoice_origin, ref1

        # Outgoing refunds will use the sale.order reference from the reversed invoice
        if move.move_type == "out_refund" and move.reversed_entry_id.invoice_origin:
            return move.reversed_entry_id.invoice_origin, ref1

        # Use refund reference if unequal to ref1
        if move.move_type == "out_refund" and move.name != ref1:
            return move.name, ref1

        # All non-entry will use the default
        if move.move_type != "entry":
            return ref1, ref2

        # Try to find the reconciled invoices
        matching = move.mapped("line_ids.full_reconcile_id.reconciled_line_ids.move_id")
        if not matching:
            return ref1, ref2

        # First invoices if possible
        domain = [("move_type", "=like", "%_invoice")]
        invs = matching.filtered_domain(domain)
        if len(invs) == 1:
            return self._get_matching_references(invs, ref1, ref2)

        # Fall back to refunds if possible
        domain = [("move_type", "=like", "%_refund")]
        invs = matching.filtered_domain(domain)
        if len(invs) == 1:
            return self._get_matching_references(
                invs.reversed_entry_id or invs, ref1, ref2
            )

        # Fall back to the default
        return ref1, ref2

    def _get_data_transaction(self, move):
        for data in super()._get_data_transaction(move):
            ref1, ref2 = self._get_matching_references(move, move.name, "")
            data.update({"Belegfeld 1": ref1, "Belegfeld 2": ref2})

            if move.partner_id.name:
                data["Buchungstext"] += " " + move.partner_id.name
            yield data
