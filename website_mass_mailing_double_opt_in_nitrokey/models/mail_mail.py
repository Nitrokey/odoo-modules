# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, tools


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _send_prepare_values(self, partner=None):
        # TDE: temporary addition (mail was parameter) due to semi-new-API
        res = super()._send_prepare_values(partner)
        if self.mailing_id and res.get("body") and res.get("email_to"):
            base_url = self.mailing_id.get_base_url()
            emails = tools.email_split(res.get("email_to")[0])
            email_to = emails and emails[0] or False

            urls_to_replace = [
                (
                    base_url + "/unsubscribe_from_list",
                    self.mailing_id._get_unsubscribe_url(email_to, self.res_id),
                ),
                (
                    base_url + "/view",
                    self.mailing_id._get_view_url(email_to, self.res_id),
                ),
            ]

            for url_to_replace, new_url in urls_to_replace:
                if url_to_replace in res["body_alternative"]:
                    res["body_alternative"] = res["body_alternative"].replace(
                        url_to_replace, new_url if new_url else "#"
                    )
        return res
