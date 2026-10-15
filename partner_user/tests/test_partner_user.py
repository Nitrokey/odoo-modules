from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPartnerUser(TransactionCase):
    def test_view_registered(self):
        view = self.env.ref("partner_user.res_partner_view_form_syscoon")
        self.assertEqual(view.model, "res.partner")
        self.assertEqual(view.inherit_id, self.env.ref("base.view_partner_form"))

    def test_user_ids_field_in_form_view(self):
        result = self.env["res.partner"].get_view(
            self.env.ref("base.view_partner_form").id, "form"
        )
        arch = etree.fromstring(result["arch"])
        fields_ = arch.xpath("//field[@name='user_ids']")
        self.assertTrue(fields_, "user_ids must be shown in the partner form")
        self.assertEqual(fields_[0].get("widget"), "many2many_tags")
        self.assertIn("user_ids", result["models"]["res.partner"])

    def test_default_form_view_includes_field(self):
        result = self.env["res.partner"].get_view(view_type="form")
        arch = etree.fromstring(result["arch"])
        self.assertTrue(arch.xpath("//field[@name='user_ids']"))

    def test_user_ids_value(self):
        user = self.env["res.users"].create({"name": "PU", "login": "partner_user_t"})
        partner = user.partner_id
        self.assertEqual(partner.user_ids, user)
        self.assertIn("user_ids", partner._fields)
