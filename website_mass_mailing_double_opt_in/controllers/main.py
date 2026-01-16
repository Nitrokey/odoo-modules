# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import uuid

from odoo import tools
from odoo.http import Controller, request, route

from odoo.addons.mass_mailing.controllers.main import MassMailController

_logger = logging.getLogger(__name__)


class MassMailController(MassMailController):
    @staticmethod
    def subscribe_to_newsletter(
        subscription_type, value, list_id, fname, address_name=None
    ):
        subscription = request.env["mailing.subscription"].sudo()
        ContactSubscription = request.env["mailing.subscription"].sudo()
        Contacts = request.env["mailing.contact"].sudo()
        if subscription_type == "email":
            name, value = tools.parse_contact_from_email(value)
            if not name:
                name = address_name
        elif subscription_type == "mobile":
            name = value

        subscription = ContactSubscription.search(
            [("list_id", "=", int(list_id)), (f"contact_id.{fname}", "=", value)],
            limit=1,
        )
        if not subscription:
            # inline add_to_list as we've already called half of it
            # Customisation Start
            contact_id = Contacts.search([(fname, "=", value)], limit=1)
            language = request.lang.code
            if subscription_type == "email":
                created = False
                if not contact_id:
                    contact_id = Contacts.create({"name": name, fname: value})
                    created = True
                domain = [("contact_id", "=", contact_id.id), ("list_id", "=", list_id)]
                mailing_list_contact = ContactSubscription.search(domain)

                if not mailing_list_contact:
                    created = True
                    mailing_list_contact = ContactSubscription.create(
                        {
                            "contact_id": contact_id.id,
                            "list_id": list_id,
                            "opt_out": True,
                        }
                    )

                created = True
                if created:
                    mailing_list_contact.write(
                        {
                            "opt_out": True,
                            "access_token": str(uuid.uuid4().hex),
                            "mail_language": language,
                        }
                    )
                    template = mailing_list_contact.double_opt_in_mail_template().sudo()
                    template.with_context(lang=language).send_mail(
                        mailing_list_contact.id, force_send=True
                    )
            else:
                # Customisation End
                ContactSubscription.create(
                    {"contact_id": contact_id.id, "list_id": int(list_id)}
                )
        elif subscription.opt_out:
            subscription.opt_out = False
        # add email to session
        request.session[f"mass_mailing_{fname}"] = value


class ConsentController(Controller):
    def consent_success(self):
        """Successful consent to redirect to different sides if required"""
        base_url = request.httprequest.host_url.rstrip("/")
        redirect_url = base_url + "/subscribed"
        return request.redirect(redirect_url)

    def consent_failure(self):
        """Redirect to a public invalid page"""
        return request.redirect("/newsletter/invalid")

    @route("/newsletter/invalid", type="http", auth="public", website=True)
    def invalid_page(self, **kwargs):
        """Public route for invalid page (uses website layout)"""
        return request.render(
            "website_mass_mailing_double_opt_in.invalid_subscription_confirmation_template"
        )

    @route("/subscribed", type="http", auth="public", website=True)
    def subscribed(self, **kwargs):
        return request.render("website_mass_mailing_double_opt_in.subscribe_newsletter")

    @route(
        "/newsletter/confirmation/<access_token>",
        type="http",
        auth="none",
        website=True,
    )
    def consent(self, access_token, **kwargs):
        try:
            mailing_list_contact = (
                request.env["mailing.subscription"]
                .sudo()
                .search([("access_token", "=", access_token)], limit=1)
            )
            if not mailing_list_contact:
                _logger.warning(
                    "No mailing subscription found for access token: %s", access_token
                )
                return self.consent_failure()

            mailing_list_contact.write({"opt_out": False})
            template = mailing_list_contact.consent_mail_template().sudo()
            if not template:
                _logger.warning(
                    "No consent mail template found for subscription ID: %s",
                    mailing_list_contact.id,
                )
                return self.consent_failure()

            # Send email with explicit user context for template rendering
            language = mailing_list_contact.mail_language or request.lang.code
            template.sudo().with_context(lang=language).send_mail(
                mailing_list_contact.id, force_send=True
            )

            return self.consent_success()

        except Exception as e:
            _logger.error("Error processing newsletter confirmation: %s", str(e))
            return self.consent_failure()
