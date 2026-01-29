import re

from odoo import _, api, models


class DatevXmlGenerator(models.AbstractModel):
    _inherit = "datev.xml.generator"

    @api.model
    def _check_invoices(self, invoices):
        for invoice in invoices:
            self._check_partner_data(invoice)
        return super()._check_invoices(invoices)

    def _check_partner_data(self, invoice):
        """Check partner data for invalid characters that would break XML export."""

        # Define control characters and other problematic characters for XML
        # This includes ASCII control characters (0x00-0x1F except tab, newline, CR)
        # and other characters that can cause XML parsing issues
        invalid_chars_pattern = r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]"

        def check_field(field_value, field_name, partner_name):
            if field_value and re.search(invalid_chars_pattern, field_value):
                # Find the specific invalid characters for better error reporting
                invalid_chars = set(re.findall(invalid_chars_pattern, field_value))
                char_codes = [f"U+{ord(char):04X}" for char in invalid_chars]
                raise ValueError(
                    self.env._(
                        "Partner '%(partner)s' contains invalid characters "
                        "in %(field)s: %(chars)s. "
                        "These characters cannot be exported to DATEV XML format.",
                        partner=partner_name,
                        field=field_name,
                        chars=", ".join(char_codes),
                    )
                )

        # Check both invoice partner and company partner (supplier)
        partners_to_check = []

        if invoice.move_type in ["out_invoice", "out_refund"]:
            # For outgoing invoices: check customer (invoice_party) and company
            # (supplier_party)
            partners_to_check.append((invoice.partner_id, _("Customer")))
            partners_to_check.append((invoice.company_id.partner_id, _("Company")))
        else:
            # For incoming invoices: check vendor (supplier_party) and company
            # (invoice_party)
            partners_to_check.append((invoice.partner_id, _("Vendor")))
            partners_to_check.append((invoice.company_id.partner_id, _("Company")))

        for partner, partner_type in partners_to_check:
            if not partner:
                continue

            partner_name = (
                f"{partner_type} ({partner.display_name or partner.name or 'Unknown'})"
            )

            # Check the fields that are used in the XML template
            check_field(partner.display_name, "name", partner_name)
            check_field(partner.name, "name", partner_name)
            check_field(partner.street, "street address", partner_name)
            check_field(partner.street2, "street address (line 2)", partner_name)
            check_field(partner.city, "city", partner_name)
            check_field(partner.zip, "postal code", partner_name)

            # Also check bank account information if present
            for bank in partner.bank_ids:
                if bank.bank_id:
                    check_field(bank.bank_id.name, "bank name", partner_name)
