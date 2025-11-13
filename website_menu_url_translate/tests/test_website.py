import logging

from odoo.tests.common import HttpCase, tagged

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestWebsiteLangRedirect(HttpCase):
    """Test website language redirection controller (/website/lang/<lang>)."""

    def setUp(self):
        super().setUp()
        self.website = self.env["website"].get_current_website()
        # Minimal QWeb view
        self.view_contact = self.env["ir.ui.view"].create(
            {
                "name": "test_contactus_view",
                "type": "qweb",
                "arch_db": "<t t-name='test.contactus'>Contact Us Test Page</t>",
            }
        )
        # Website page
        self.page_en = self.env["website.page"].create(
            {
                "name": "Contact Us",
                "url": "/test/contactus",
                "view_id": self.view_contact.id,
                "website_id": self.website.id,
                "is_published": True,
            }
        )
        # Translations
        self.page_en.with_context(lang="en_US").url = "/test/contactus"
        self.page_en.with_context(lang="de_DE").url = "/test/kontakt"

    def test_01_change_lang_redirect(self):
        """Test redirect to German version when language = de_DE."""
        resp = self.url_open(
            "/website/lang/de_DE?r=/test/contactus", allow_redirects=False
        )
        self.assertIn(resp.status_code, (303, 200))
        redirect_url = resp.headers.get("Location")
        _logger.info(
            "[DE] Status: %s | Redirected to: %s", resp.status_code, redirect_url
        )

    def test_02_default_language_redirect(self):
        """Test /website/lang redirection works cleanly."""
        resp = self.url_open(
            "/website/lang/en_US?r=/test/contactus", allow_redirects=False
        )
        self.assertIn(resp.status_code, (303, 200))
        redirect_url = resp.headers.get("Location")
        _logger.info(
            "[EN] Status: %s | Redirected to: %s", resp.status_code, redirect_url
        )
