# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import uuid

from odoo import fields, models, tools


class MailingSubscription(models.Model):
    _inherit = "mailing.subscription"

    access_token = fields.Char(copy=False)
    mail_language = fields.Char()

    def double_opt_in_mail_template(self):
        return self.env.ref(
            "website_mass_mailing_double_opt_in.newsletter_confirmation_request_template"
        )

    def double_opt_in_subscribe(self, list_id, email, language):
        contacts = self.env["mailing.contact"]
        name, email = tools.parse_contact_from_email(email)

        existing_contact = contacts.search(
            [("list_ids", "=", list_id), ("email", "=", email)], limit=1
        )
        if existing_contact.opt_out:
            existing_contact.opt_out = False
            return email

        # inline add_to_list as we've already called half of it
        contact = contacts.search([("email", "=", email)], limit=1)
        created = False
        if not contact:
            contact = contacts.create({"name": name, "email": email})
            created = True

        domain = [("contact_id", "=", contact.id), ("list_id", "=", list_id)]
        mailing_list_contact = self.search(domain)

        if not mailing_list_contact:
            created = True
            mailing_list_contact = self.create(
                {"contact_id": contact.id, "list_id": list_id, "opt_out": True}
            )

        if created:
            mailing_list_contact.write(
                {
                    "opt_out": True,
                    "access_token": str(uuid.uuid4().hex),
                    "mail_language": language,
                }
            )
            template = self.double_opt_in_mail_template().sudo()
            template.with_context(lang=language).send_mail(
                mailing_list_contact.id, force_send=True
            )

        return email
