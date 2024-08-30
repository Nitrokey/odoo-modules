import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _unique_key_for_mail(self):
        active_model = self.env.context.get("active_model")
        return self.model or active_model

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
            rec._unique_key_for_model(model): rec
            for rec in (email_froms - to_keep).sorted("sequence", True)
            for model in rec.mapped("model_ids.model")
        }

        # Default
        domain = [("action", "=", "set"), ("model_ids", "=", False)]
        default = email_froms.filtered_domain(domain)[:1]

        to_keep = {
            rec._unique_key_for_model(model)
            for rec in to_keep
            for model in rec.mapped("model_ids.model")
        }

        for mail in res:
            key = mail._unique_key_for_mail()

            rec = to_adjust.get(key, default)
            if rec and key not in to_keep:
                mail.write({"email_from": rec.email_from})
                mail.write({"reply_to": rec.email_from})

        return res
