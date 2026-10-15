# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDoubleOptInSubscribe(TransactionCase):
    """Test the model side of the double opt-in flow"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mailing_list = cls.env["mailing.list"].create({"name": "DOI list"})
        cls.other_list = cls.env["mailing.list"].create({"name": "DOI other list"})
        cls.subscription_model = cls.env["mailing.subscription"]

    def _subscribe(self, email, list_=None, language="en_US"):
        """Subscribe with the mail sending mocked, return (result, mock)"""
        list_ = list_ or self.mailing_list
        mail_template_model = type(self.env["mail.template"])
        with patch.object(mail_template_model, "send_mail") as send_mail:
            result = self.subscription_model.double_opt_in_subscribe(
                list_.id, email, language
            )
        return result, send_mail

    def _get_subscription(self, email, list_=None):
        list_ = list_ or self.mailing_list
        return self.subscription_model.search(
            [("list_id", "=", list_.id), ("contact_id.email", "=", email)]
        )

    def test_mail_template(self):
        template = self.subscription_model.double_opt_in_mail_template()
        self.assertEqual(template._name, "mail.template")
        self.assertEqual(template.model, "mailing.subscription")

    def test_new_contact(self):
        # not de_DE: website_mass_mailing_double_opt_in_nitrokey changes the list
        result, send_mail = self._subscribe("new.contact@example.com", language="fr_FR")
        self.assertEqual(result, "new.contact@example.com")

        subscription = self._get_subscription("new.contact@example.com")
        self.assertEqual(len(subscription), 1)
        self.assertTrue(subscription.opt_out, "Not confirmed yet")
        self.assertEqual(len(subscription.access_token), 32)
        self.assertEqual(subscription.mail_language, "fr_FR")

        send_mail.assert_called_once()
        self.assertEqual(send_mail.call_args.args[0], subscription.id)
        self.assertTrue(send_mail.call_args.kwargs["force_send"])

    def test_new_contact_with_name(self):
        result, send_mail = self._subscribe('"John Doe" <john.doe@example.com>')
        self.assertEqual(result, "john.doe@example.com")
        subscription = self._get_subscription("john.doe@example.com")
        self.assertEqual(subscription.contact_id.name, "John Doe")
        send_mail.assert_called_once()

    def test_existing_contact_other_list(self):
        contact = self.env["mailing.contact"].create(
            {
                "name": "Existing",
                "email": "existing@example.com",
                "list_ids": [(6, 0, self.other_list.ids)],
            }
        )
        result, send_mail = self._subscribe("existing@example.com")
        self.assertEqual(result, "existing@example.com")
        subscription = self._get_subscription("existing@example.com")
        self.assertEqual(subscription.contact_id, contact)
        self.assertTrue(subscription.opt_out)
        self.assertTrue(subscription.access_token)
        send_mail.assert_called_once()
        # The other subscription is untouched
        other = self._get_subscription("existing@example.com", self.other_list)
        self.assertFalse(other.opt_out)
        self.assertFalse(other.access_token)

    def test_existing_confirmed_subscription(self):
        self.env["mailing.contact"].create(
            {
                "name": "Confirmed",
                "email": "confirmed@example.com",
                "list_ids": [(6, 0, self.mailing_list.ids)],
            }
        )
        result, send_mail = self._subscribe("confirmed@example.com")
        self.assertEqual(result, "confirmed@example.com")
        subscription = self._get_subscription("confirmed@example.com")
        self.assertFalse(subscription.opt_out)
        self.assertFalse(subscription.access_token)
        send_mail.assert_not_called()

    def test_existing_pending_subscription(self):
        """A repeated request resends the mail but never confirms by itself"""
        self._subscribe("pending@example.com", language="en_US")
        subscription = self._get_subscription("pending@example.com")
        token = subscription.access_token

        result, send_mail = self._subscribe("pending@example.com", language="fr_FR")
        self.assertEqual(result, "pending@example.com")
        self.assertTrue(subscription.opt_out)
        # the token of the first mail stays valid
        self.assertEqual(subscription.access_token, token)
        self.assertEqual(subscription.mail_language, "fr_FR")
        send_mail.assert_called_once()
        self.assertEqual(send_mail.call_args.args[0], subscription.id)

    def test_access_token_not_copied(self):
        self._subscribe("copy@example.com")
        subscription = self._get_subscription("copy@example.com")
        self.assertTrue(subscription.access_token)
        self.assertFalse(subscription.copy_data()[0].get("access_token"))

    def test_send_mail_renders_confirmation_link(self):
        """The real template contains the token link"""
        self._subscribe("render@example.com")
        subscription = self._get_subscription("render@example.com")
        template = self.subscription_model.double_opt_in_mail_template()
        body = template._render_field("body_html", subscription.ids)[subscription.id]
        self.assertIn(
            f"/newsletter/confirmation/{subscription.access_token}", str(body)
        )
        subject = template._render_field("subject", subscription.ids)[subscription.id]
        self.assertTrue(subject)


@tagged("post_install", "-at_install")
class TestDoubleOptInController(HttpCase):
    """Test the HTTP controllers of the double opt-in flow"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mailing_list = cls.env["mailing.list"].create({"name": "DOI HTTP list"})

    def _create_pending_subscription(self, email, language="en_US", token="abc123"):
        contact = self.env["mailing.contact"].create(
            {"name": "Pending", "email": email}
        )
        return self.env["mailing.subscription"].create(
            {
                "contact_id": contact.id,
                "list_id": self.mailing_list.id,
                "opt_out": True,
                "access_token": token,
                "mail_language": language,
            }
        )

    def _recaptcha(self, result):
        return patch.object(
            type(self.env["ir.http"]),
            "_verify_request_recaptcha_token",
            return_value=result,
        )

    def _subscribe_params(self, email, **extra):
        return {
            "list_id": self.mailing_list.id,
            "value": email,
            "subscription_type": "email",
            **extra,
        }

    # Pages

    def test_invalid_page(self):
        response = self.url_open("/newsletter/invalid")
        self.assertEqual(response.status_code, 200)
        self.assertIn("This confirmation link is invalid.", response.text)

    def test_subscribed_page(self):
        response = self.url_open("/subscribed")
        self.assertEqual(response.status_code, 200)
        self.assertIn("You have subscribed to the newsletter.", response.text)

    # Subscribe route

    def test_subscribe_email(self):
        mail_template_model = type(self.env["mail.template"])
        with (
            self._recaptcha(True),
            patch.object(mail_template_model, "send_mail") as send_mail,
        ):
            result = self.make_jsonrpc_request(
                "/website_mass_mailing/subscribe",
                self._subscribe_params("http.new@example.com", language="fr_FR"),
            )
        self.assertEqual(result["toast_type"], "success")
        subscription = self.env["mailing.subscription"].search(
            [
                ("list_id", "=", self.mailing_list.id),
                ("contact_id.email", "=", "http.new@example.com"),
            ]
        )
        self.assertEqual(len(subscription), 1)
        self.assertTrue(subscription.opt_out)
        self.assertTrue(subscription.access_token)
        self.assertEqual(subscription.mail_language, "fr_FR")
        send_mail.assert_called_once()

    def test_subscribe_email_default_language(self):
        mail_template_model = type(self.env["mail.template"])
        with self._recaptcha(True), patch.object(mail_template_model, "send_mail"):
            result = self.make_jsonrpc_request(
                "/website_mass_mailing/subscribe",
                self._subscribe_params("http.lang@example.com"),
            )
        self.assertEqual(result["toast_type"], "success")
        subscription = self.env["mailing.subscription"].search(
            [("contact_id.email", "=", "http.lang@example.com")]
        )
        self.assertTrue(subscription.mail_language)

    def test_subscribe_recaptcha_failure(self):
        with self._recaptcha(False):
            result = self.make_jsonrpc_request(
                "/website_mass_mailing/subscribe",
                self._subscribe_params("http.captcha@example.com"),
            )
        self.assertEqual(result["toast_type"], "danger")
        self.assertFalse(
            self.env["mailing.contact"].search(
                [("email", "=", "http.captcha@example.com")]
            )
        )

    # Confirmation route

    def test_consent_unknown_token(self):
        response = self.url_open(
            "/newsletter/confirmation/does-not-exist", allow_redirects=False
        )
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers["Location"].endswith("/newsletter/invalid"))

    def test_consent_success(self):
        subscription = self._create_pending_subscription(
            "consent.en@example.com", language="en_US", token="tok-en"
        )
        response = self.url_open(
            "/newsletter/confirmation/tok-en", allow_redirects=False
        )
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers["Location"].endswith("/subscribed"))
        subscription.invalidate_recordset()
        self.assertFalse(subscription.opt_out)

        mail = self.env["mail.mail"].search(
            [("email_to", "=", "consent.en@example.com")]
        )
        self.assertEqual(len(mail), 1)
        self.assertIn("Subscribed", mail.subject)
        self.assertIn("Thank you", mail.body_html)

    def test_consent_success_german(self):
        subscription = self._create_pending_subscription(
            "consent.de@example.com", language="de_DE", token="tok-de"
        )
        response = self.url_open(
            "/newsletter/confirmation/tok-de", allow_redirects=False
        )
        self.assertIn(response.status_code, (301, 302, 303))
        subscription.invalidate_recordset()
        self.assertFalse(subscription.opt_out)

        mail = self.env["mail.mail"].search(
            [("email_to", "=", "consent.de@example.com")]
        )
        self.assertEqual(len(mail), 1)
        self.assertIn("abonniert", mail.subject)
        self.assertTrue(mail.body_html)

    def test_consent_other_language(self):
        subscription = self._create_pending_subscription(
            "consent.fr@example.com", language="fr_FR", token="tok-fr"
        )
        response = self.url_open(
            "/newsletter/confirmation/tok-fr", allow_redirects=False
        )
        self.assertIn(response.status_code, (301, 302, 303))
        subscription.invalidate_recordset()
        self.assertFalse(subscription.opt_out)
        mail = self.env["mail.mail"].search(
            [("email_to", "=", "consent.fr@example.com")]
        )
        self.assertEqual(len(mail), 1)

    def test_consent_mail_failure_still_confirms(self):
        subscription = self._create_pending_subscription(
            "consent.fail@example.com", token="tok-fail"
        )
        mail_model = type(self.env["mail.mail"])
        with patch.object(mail_model, "send", side_effect=Exception("SMTP down")):
            response = self.url_open(
                "/newsletter/confirmation/tok-fail", allow_redirects=False
            )
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers["Location"].endswith("/subscribed"))
        subscription.invalidate_recordset()
        self.assertFalse(subscription.opt_out)

    def test_consent_unexpected_error(self):
        self._create_pending_subscription("consent.err@example.com", token="tok-err")
        subscription_model = type(self.env["mailing.subscription"])
        with patch.object(
            subscription_model, "write", side_effect=ValueError("unexpected")
        ):
            response = self.url_open(
                "/newsletter/confirmation/tok-err", allow_redirects=False
            )
        self.assertIn(response.status_code, (301, 302, 303))
        self.assertTrue(response.headers["Location"].endswith("/newsletter/invalid"))
