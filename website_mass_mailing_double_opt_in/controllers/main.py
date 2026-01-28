# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _
from odoo.http import Controller, request, route

from odoo.addons.mass_mailing.controllers.main import MassMailController

_logger = logging.getLogger(__name__)


class MassMailController(MassMailController):
    @route("/website_mass_mailing/subscribe", type="json", website=True, auth="public")
    def subscribe(self, list_id, value, subscription_type, **post):
        if not request.env["ir.http"]._verify_request_recaptcha_token(
            "website_mass_mailing_subscribe"
        ):
            return {
                "toast_type": "danger",
                "toast_content": _("Suspicious activity detected by Google reCaptcha."),
            }

        fname = self._get_fname(subscription_type)
        # Customisation Start
        if subscription_type == "email":
            subscription = request.env["mailing.subscription"].sudo()
            # add email to session
            request.session["mass_mailing_email"] = (
                subscription.double_opt_in_subscribe(
                    list_id,
                    value,
                    language=post.get("language") or request.lang.code,
                )
            )
        else:
            self.subscribe_to_newsletter(subscription_type, value, list_id, fname)
        # Customisation End
        return {
            "toast_type": "success",
            "toast_content": _("Thanks for subscribing!"),
        }


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
            if not request.env.user:
                request.env.user = mailing_list_contact.create_uid
            template.with_context(
                lang=language,
            ).send_mail(
                mailing_list_contact.id,
                force_send=True,
                email_values={"email_from": mailing_list_contact.contact_id.email},
            )

            return self.consent_success()

        except Exception as e:
            _logger.error("Error processing newsletter confirmation: %s", str(e))
            return self.consent_failure()
