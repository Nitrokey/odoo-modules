# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import uuid

from odoo import fields, models


class MailingSubscription(models.Model):
    _inherit = "mailing.subscription"

    access_token = fields.Char(copy=False)
    mail_language = fields.Char()

    def double_opt_in_mail_template(self):
        return self.env.ref(
            "website_mass_mailing_double_opt_in.newsletter_confirmation_request_template"
        )

    def consent_mail_template(self):
        return self.env.ref(
            "website_mass_mailing_double_opt_in.newsletter_confirmation_success_template"
        )
