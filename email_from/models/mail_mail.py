from odoo import api, models


class MailMail(models.Model):
    _inherit = "mail.mail"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        email_froms = self.env.company.email_from_ids.sudo().filtered("active")

        # Get the models to keep without change
        domain = [("action", "=", "keep")]
        to_keep = email_froms.filtered_domain(domain)

        # Prepare a mapping for the adjustments. Reverse the order to keep the
        # highest priority record
        to_adjust = {
            model: rec
            for rec in (email_froms - to_keep).sorted("sequence", True)
            for model in rec.mapped("model_ids.model")
        }

        # Default
        domain = [("action", "=", "set"), ("model_ids", "=", False)]
        default = email_froms.filtered_domain(domain)[:1]

        # Apply the mapping of the adjustments
        domain = [
            ("model", "not in", to_keep.mapped("model_ids.model")),
            ("email_from", "!=", False),
        ]
        for mail in res.filtered_domain(domain):
            rec = to_adjust.get(mail.model, default)
            if rec:
                mail.write({"email_from": rec.email_from})

        return res
