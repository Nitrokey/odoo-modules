# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def datev_invoice_id(self):
        """Custom overwrite for the NK special case"""
        self.ensure_one()

        if self.move_type not in (
            "in_invoice",
            "in_refund",
            "out_invoice",
            "out_refund",
        ):
            return self.datev_sanitize(self.name or "")

        reference = self.name or ""
        if self.move_type.startswith("in_") and self.ref:
            reference = self.ref
        elif self.move_type == "out_invoice" and self.invoice_origin:
            reference = self.invoice_origin
        elif self.move_type == "out_refund" and self.reversed_entry_id.invoice_origin:
            reference = self.reversed_entry_id.invoice_origin

        return self.datev_sanitize(reference)

    def datev_order_id(self):
        self.ensure_one()
        return self.datev_sanitize(self.name or "")
