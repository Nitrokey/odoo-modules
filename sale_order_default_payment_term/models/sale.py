from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_payment_term_id(self):
        """Set the first payment term as default when creating a new sales order."""
        # Get the first payment term from the system using default ordering (sequence, id)
        first_payment_term = self.env["account.payment.term"].search([], limit=1)
        return first_payment_term

    @api.model
    def create(self, vals):
        """Override create to set default payment term if needed."""
        # If partner_id is provided but payment_term_id is not
        if vals.get("partner_id") and not vals.get("payment_term_id"):
            # Check if partner has a payment term
            partner = self.env["res.partner"].browse(vals["partner_id"])
            if partner.property_payment_term_id:
                # Use partner's payment term
                vals["payment_term_id"] = partner.property_payment_term_id.id
            else:
                # Use our default
                vals["payment_term_id"] = self._default_payment_term_id().id

        return super().create(vals)
