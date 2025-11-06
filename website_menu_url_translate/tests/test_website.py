# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo.tests.common import HttpCase, TransactionCase

CONTROLLER_PATH = "odoo.addons.website_sale_affiliate.controllers.main"


class WebsiteSaleCase(HttpCase, TransactionCase):
    def setUp(self):
        super().setUp()
        self.test1 = self.env.ref("website_menu_url_translate.lang_change_test_1")
        self.test2 = self.env.ref("website_menu_url_translate.lang_change_test_2")

    def test_change_lang(self):
        """Test change_lang controller with multiple languages"""
        # Test with default language
        req = self.url_open("/website/lang/default", allow_redirects=False)
        self.assertIn(req.status_code, [303, 200])

        # Test with English language
        req = self.url_open("/website/lang/en_US?r=testen", allow_redirects=False)
        self.assertIn(req.status_code, [303, 200])

        # Test with German language
        req = self.url_open("/website/lang/de_DE?r=Testing", allow_redirects=False)
        self.assertIn(req.status_code, [303, 200])

        # Test with Spanish language
        req = self.url_open("/website/lang/es_ES?r=", allow_redirects=False)
        self.assertIn(req.status_code, [303, 200])

        # Test with English language (empty route)
        req = self.url_open("/website/lang/en_US?r=", allow_redirects=False)
        self.assertIn(req.status_code, [303, 200])

        # Test with German language (empty route)
        req = self.url_open("/website/lang/de_DE?r=", allow_redirects=False)
        self.assertIn(req.status_code, [303, 200])
