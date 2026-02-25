# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, http
from odoo.http import request

from odoo.addons.website_mass_mailing_double_opt_in.controllers.main import (
    ConsentController,
)
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.payment import PaymentPortal

_logger = logging.getLogger(__name__)


class ConsentControllerExt(ConsentController):
    def consent_success(self):
        return request.redirect("https://www.nitrokey.com/subscribed")

    def _prepare_mail_content(self, mailing_list_contact, language):
        """Newsletter Subscribed email template content"""
        res = super()._prepare_mail_content(mailing_list_contact, language)
        # Get company information
        user = request.env.user
        company = user.company_id or request.env.company
        # Update subject
        res["subject"] = _("You Have Subscribed to the Nitrokey Newsletter")
        # Get translated strings for body header
        greeting = _("Hi!")
        thank_you = _("Thank you for subscribing the Nitrokey newsletter.")
        best_regards = _("Best regards,")
        team = _("your Nitrokey team")
        # Build complete HTML with a single f-string
        res["body_html"] = f"""
            <div>
                <p>{greeting}</p>
                <p>{thank_you}</p>
                <br />
                <p>{best_regards}<br />{team}</p>
            </div>

            <div>
                <div style="max-width: 532px; background-color: #14212D;">
                    <table style="margin-left: 15px;">
                        <tr>
                            <td colspan="2"
                                style="color: #FFFFFF;
                                       font-family: Arial;
                                       font-size: 13px;
                                       line-height: 17px;">
                                <br />
                                <strong>{company.name or ''}</strong><br />

                                {company.street or ''} {company.street2 or ''}<br />
                                {company.zip or ''} {company.city or ''}<br />
                                {company.state_id.name if company.state_id else ''}
                                {company.country_id.name if company.country_id else ''}

                                <br /><br />
                                <strong>CEO:</strong>
                                {company.ceo or ''}<br />
                                <strong>Company register:</strong>
                                {company.company_registry or ''}<br />
                                <strong>VAT ID:</strong>
                                {company.vat or ''}
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
        """
        return res


class PaymentPortalExt(PaymentPortal):
    @http.route(
        "/shop/payment/transaction/<int:order_id>",
        type="json",
        auth="public",
        website=True,
    )
    def shop_payment_transaction(self, *args, **kwargs):
        """Payment transaction override to double check cart quantities before
        placing the order
        """
        order = request.website.sale_get_order()
        is_subscribed = order.partner_id.newsletter_subscribed
        if not is_subscribed or not order.partner_id.email:
            return super().shop_payment_transaction(*args, **kwargs)

        # Automatically subscribe the newsletter if the option
        # Stay informed about the project progress, new products and firmware updates.
        # is selected by the customer.
        newsletter = request.env.ref("mass_mailing.mailing_list_data")
        subscription = request.env["mailing.subscription"].sudo()
        request.session["mass_mailing_email"] = subscription.double_opt_in_subscribe(
            newsletter.id,
            order.partner_id.email,
            language=request.lang.code,
        )
        return super().shop_payment_transaction(*args, **kwargs)


class WebsiteSaleExt(WebsiteSale):
    def _prepare_checkout_page_values(self, order_sudo, **_kwargs):
        res = super()._prepare_checkout_page_values(order_sudo, **_kwargs)
        if res and res.get("checkout"):
            res["checkout"]["newsletter"] = res.get("newsletter") == "on"
        return res

    def _handle_extra_form_data(self, extra_form_data, address_values):
        res = super()._handle_extra_form_data(extra_form_data, address_values)
        if extra_form_data.get("newsletter") and address_values.get("email"):
            subscription = request.env["mailing.subscription"].sudo()
            subscription.double_opt_in_subscribe(
                request.website.newsletter_id.id,
                address_values.get("email"),
                language=request.lang.code,
            )
        return res
