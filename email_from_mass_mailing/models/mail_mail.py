import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _map_records(self, email_froms):
        # Filter out apply_to_mailing records
        email_froms_mailing = email_froms.filtered("apply_to_mailing")

        return super()._map_records(email_froms - email_froms_mailing)

    def _filter_records(self, recs):
        return recs - recs.filtered("mailing_id")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        # Handle apply_to_mailing records
        email_froms = (
            self.env.company.email_from_ids.sudo()
            .filtered("active")
            .filtered("apply_to_mailing")
        )

        domain = [("action", "=", "keep")]
        to_keep = email_froms.filtered_domain(domain)
        to_adjust = {
            model: rec
            for rec in (email_froms - to_keep).sorted("sequence", True)
            for model in rec.mapped("model_ids.model")
        }

        # Default
        domain = [("action", "=", "set"), ("model_ids", "=", False)]
        default = email_froms.filtered_domain(domain)[:1]

        to_keep = to_keep.mapped("model_ids.model")

        active_model = self.env.context.get("active_model")
        # Apply the mapping of the adjustments
        domain = [("model", "not in", to_keep), ("mailing_id", "!=", False)]
        if active_model in to_keep:
            domain.append(("model", "!=", False))

        for mail in res.filtered_domain(domain):
            model = res.mailing_id.mailing_model_id.model

            rec = to_adjust.get(model, default)
            if rec:
                mail.write({"email_from": rec.email_from})

        return res
