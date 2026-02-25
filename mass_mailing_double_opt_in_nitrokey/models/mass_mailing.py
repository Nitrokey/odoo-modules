# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailingSubscription(models.Model):
    _inherit = "mailing.subscription"

    def double_opt_in_mail_template(self):
        return self.env.ref(
            "mass_mailing_double_opt_in_nitrokey.nitrokey_newsletter_confirmation_request_template"
        )

    def double_opt_in_subscribe(self, list_id, email, language):
        if language == "de_DE":
            list_id = self.env.ref("nitrokey_setup.german_newsletter_mass_mail_list").id
        return super().double_opt_in_subscribe(list_id, email, language)
