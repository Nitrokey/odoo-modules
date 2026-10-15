# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.website.tools import MockRequest
from odoo.addons.website_mass_mailing_double_opt_in_nitrokey.controllers.main import (
    ConsentControllerExt,
    PaymentPortalExt,
    WebsiteSaleExt,
)
from odoo.addons.website_sale.controllers.payment import PaymentPortal


@tagged("post_install", "-at_install")
class TestMailingSubscription(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.subscription_model = cls.env["mailing.subscription"]
        cls.english_list = cls.env["mailing.list"].create({"name": "Nitrokey EN test"})
        cls.german_list = cls.env.ref("nitrokey_setup.german_newsletter_mass_mail_list")

    def _subscribe(self, email, language, list_=None):
        list_ = list_ or self.english_list
        mail_template_model = type(self.env["mail.template"])
        with patch.object(mail_template_model, "send_mail", autospec=True) as send_mail:
            result = self.subscription_model.double_opt_in_subscribe(
                list_.id, email, language
            )
        return result, send_mail

    def test_mail_template(self):
        template = self.subscription_model.double_opt_in_mail_template()
        self.assertEqual(
            template,
            self.env.ref(
                "website_mass_mailing_double_opt_in_nitrokey."
                "nitrokey_newsletter_confirmation_request_template"
            ),
        )

    def test_subscribe_english_keeps_list(self):
        result, send_mail = self._subscribe("nk.en@example.com", "en_US")
        self.assertEqual(result, "nk.en@example.com")
        subscription = self.subscription_model.search(
            [("contact_id.email", "=", "nk.en@example.com")]
        )
        self.assertEqual(subscription.list_id, self.english_list)
        self.assertTrue(subscription.opt_out)
        self.assertTrue(subscription.access_token)
        send_mail.assert_called_once()
        # The Nitrokey template is used
        self.assertEqual(
            send_mail.call_args.args[0],
            self.subscription_model.double_opt_in_mail_template(),
        )
        self.assertEqual(send_mail.call_args.args[1], subscription.id)

    def test_subscribe_german_uses_german_list(self):
        result, send_mail = self._subscribe("nk.de@example.com", "de_DE")
        self.assertEqual(result, "nk.de@example.com")
        subscription = self.subscription_model.search(
            [("contact_id.email", "=", "nk.de@example.com")]
        )
        self.assertEqual(subscription.list_id, self.german_list)
        self.assertEqual(subscription.mail_language, "de_DE")
        send_mail.assert_called_once()

    def test_confirmation_template_renders(self):
        self._subscribe("nk.render@example.com", "en_US")
        subscription = self.subscription_model.search(
            [("contact_id.email", "=", "nk.render@example.com")]
        )
        template = self.subscription_model.double_opt_in_mail_template()
        body = template._render_field("body_html", subscription.ids)[subscription.id]
        self.assertIn(
            f"/newsletter/confirmation/{subscription.access_token}", str(body)
        )

    def test_partner_newsletter_subscribed_field(self):
        partner = self.env["res.partner"].create({"name": "NK Partner"})
        self.assertFalse(partner.newsletter_subscribed)
        partner.newsletter_subscribed = True
        self.assertTrue(partner.newsletter_subscribed)


@tagged("post_install", "-at_install")
class TestControllers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("website.default_website")
        cls.mailing_list = cls.env["mailing.list"].create({"name": "NK shop list"})
        cls.website.newsletter_id = cls.mailing_list

    # ConsentControllerExt

    def _prepare_mail_content(self, language):
        contact = self.env["mailing.contact"].create(
            {"name": "Consent", "email": "consent@example.com"}
        )
        subscription = self.env["mailing.subscription"].create(
            {"contact_id": contact.id, "list_id": self.mailing_list.id}
        )
        with MockRequest(self.env, website=self.website):
            return ConsentControllerExt()._prepare_mail_content(subscription, language)

    def test_mail_content_english(self):
        values = self._prepare_mail_content("en_US")
        self.assertEqual(
            values["subject"], "You Have Subscribed to the Nitrokey Newsletter"
        )
        self.assertEqual(values["email_to"], "consent@example.com")
        self.assertIn("your Nitrokey team", values["body_html"])
        self.assertIn("CEO:", values["body_html"])
        self.assertIn("VAT ID:", values["body_html"])

    def test_mail_content_german(self):
        values = self._prepare_mail_content("de_DE")
        self.assertEqual(
            values["subject"], "Sie haben den Nitrokey Newsletter abonniert"
        )
        self.assertIn("Ihr Team", values["body_html"])
        self.assertIn("Nitrokey Newsletter abonniert", values["body_html"])

    def test_mail_content_other_language(self):
        values = self._prepare_mail_content("fr_FR")
        self.assertEqual(
            values["subject"], "You Have Subscribed to the Nitrokey Newsletter"
        )
        self.assertIn("Nitrokey", values["body_html"])

    def test_mail_content_company_details(self):
        company = self.env.company
        company.with_context(no_vat_validation=True).write(
            {"company_registry": "HRB 123456", "vat": "DE123456789"}
        )
        values = self._prepare_mail_content("en_US")
        self.assertIn("HRB 123456", values["body_html"])
        self.assertIn("DE123456789", values["body_html"])
        self.assertIn(company.name, values["body_html"])

    # PaymentPortalExt

    def _create_order(self, subscribed, email="shop.customer@example.com"):
        partner = self.env["res.partner"].create(
            {
                "name": "Shop Customer",
                "email": email,
                "newsletter_subscribed": subscribed,
            }
        )
        return self.env["sale.order"].create({"partner_id": partner.id})

    def _payment_transaction(self, order):
        website_model = type(self.env["website"])
        mail_template_model = type(self.env["mail.template"])
        with (
            MockRequest(self.env, website=self.website),
            patch.object(website_model, "sale_get_order", return_value=order),
            patch.object(
                PaymentPortal, "shop_payment_transaction", return_value={"ok": True}
            ) as parent,
            patch.object(mail_template_model, "send_mail") as send_mail,
        ):
            result = PaymentPortalExt().shop_payment_transaction(
                order.id, access_token="token"
            )
        return result, parent, send_mail

    def test_payment_transaction_subscribes(self):
        order = self._create_order(True)
        newsletter = self.env.ref("mass_mailing.mailing_list_data")
        result, parent, send_mail = self._payment_transaction(order)
        self.assertEqual(result, {"ok": True})
        parent.assert_called_once()
        subscription = self.env["mailing.subscription"].search(
            [
                ("contact_id.email", "=", "shop.customer@example.com"),
                ("list_id", "=", newsletter.id),
            ]
        )
        self.assertEqual(len(subscription), 1)
        self.assertTrue(subscription.opt_out, "Waiting for confirmation")
        send_mail.assert_called_once()

    def test_payment_transaction_not_subscribed(self):
        order = self._create_order(False)
        result, parent, send_mail = self._payment_transaction(order)
        self.assertEqual(result, {"ok": True})
        parent.assert_called_once()
        send_mail.assert_not_called()
        self.assertFalse(
            self.env["mailing.contact"].search(
                [("email", "=", "shop.customer@example.com")]
            )
        )

    def test_payment_transaction_subscribed_without_email(self):
        order = self._create_order(True, email=False)
        result, parent, send_mail = self._payment_transaction(order)
        self.assertEqual(result, {"ok": True})
        parent.assert_called_once()
        send_mail.assert_not_called()

    # WebsiteSaleExt

    def _handle_extra_form_data(self, extra_form_data, address_values):
        mail_template_model = type(self.env["mail.template"])
        with (
            MockRequest(self.env, website=self.website),
            patch.object(mail_template_model, "send_mail") as send_mail,
        ):
            WebsiteSaleExt()._handle_extra_form_data(extra_form_data, address_values)
        return send_mail

    def test_handle_extra_form_data_subscribes(self):
        send_mail = self._handle_extra_form_data(
            {"newsletter": "on"}, {"email": "address.news@example.com"}
        )
        subscription = self.env["mailing.subscription"].search(
            [("contact_id.email", "=", "address.news@example.com")]
        )
        self.assertEqual(subscription.list_id, self.mailing_list)
        self.assertTrue(subscription.opt_out)
        send_mail.assert_called_once()

    def test_handle_extra_form_data_no_newsletter(self):
        send_mail = self._handle_extra_form_data(
            {}, {"email": "address.nonews@example.com"}
        )
        send_mail.assert_not_called()
        self.assertFalse(
            self.env["mailing.contact"].search(
                [("email", "=", "address.nonews@example.com")]
            )
        )

    def test_handle_extra_form_data_no_email(self):
        send_mail = self._handle_extra_form_data({"newsletter": "on"}, {})
        send_mail.assert_not_called()


@tagged("post_install", "-at_install")
class TestConsentRedirect(HttpCase):
    def test_consent_redirects_to_nitrokey(self):
        mailing_list = self.env["mailing.list"].create({"name": "NK consent"})
        contact = self.env["mailing.contact"].create(
            {"name": "Consent", "email": "nk.consent@example.com"}
        )
        subscription = self.env["mailing.subscription"].create(
            {
                "contact_id": contact.id,
                "list_id": mailing_list.id,
                "opt_out": True,
                "access_token": "nk-token",
                "mail_language": "en_US",
            }
        )
        response = self.url_open(
            "/newsletter/confirmation/nk-token", allow_redirects=False
        )
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertEqual(
            response.headers["Location"], "https://www.nitrokey.com/subscribed"
        )
        subscription.invalidate_recordset()
        self.assertFalse(subscription.opt_out)
        mail = self.env["mail.mail"].search(
            [("email_to", "=", "nk.consent@example.com")]
        )
        self.assertEqual(len(mail), 1)
        self.assertEqual(mail.subject, "You Have Subscribed to the Nitrokey Newsletter")
