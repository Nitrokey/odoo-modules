import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _map_records(self, email_froms):
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

        return to_keep, to_adjust

    def _filter_records(self, recs):
        return recs

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        email_froms = self.env.company.email_from_ids.sudo().filtered("active")

        to_keep, to_adjust = self._map_records(email_froms)

        # Default
        domain = [("action", "=", "set"), ("model_ids", "=", False)]
        default = email_froms.filtered_domain(domain)[:1]

        to_keep = to_keep.mapped("model_ids.model")

        active_model = self.env.context.get("active_model")
        # Apply the mapping of the adjustments
        domain = [("model", "not in", to_keep)]
        if active_model in to_keep:
            domain.append(("model", "!=", False))

        for mail in self._filter_records(res.filtered_domain(domain)):
            model = res.model or active_model

            rec = to_adjust.get(model, default)
            if rec:
                mail.write({"email_from": rec.email_from})

        return res
