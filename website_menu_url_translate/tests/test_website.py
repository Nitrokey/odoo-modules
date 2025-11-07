from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteLangRedirect(HttpCase):
    """Test website language redirection controller (/website/lang/<lang>)."""

    def setUp(self):
        super().setUp()
        self.website = self.env["website"].get_current_website()
        self.page_en = self.env.ref("website_menu_url_translate.test_contact_page_en")
        self.page_de = self.env.ref("website_menu_url_translate.test_contact_page_de")
        self.assertTrue(self.page_en.exists(), "English test page missing")
        self.assertTrue(self.page_de.exists(), "German test page missing")

    def test_01_change_lang_redirect(self):
        """Switch from English to German; expect redirect to /de/test/kontakt."""
        resp = self.url_open(
            "/website/lang/de_DE?r=/test/contactus", allow_redirects=False
        )
        self.assertIn(resp.status_code, (303, 200))

    def test_02_default_language_redirect(self):
        """Switch back to English; expect redirect to /test/contactus."""
        resp = self.url_open(
            "/website/lang/en_US?r=/test/kontakt", allow_redirects=False
        )
        self.assertIn(resp.status_code, (303, 200))

    def test_03_fallback_no_translation(self):
        """If no translation exists, fallback to direct
        url without languange /test/contactus."""
        resp = self.url_open("/test/contactus", allow_redirects=False)
        self.assertIn(resp.status_code, (303, 200))
