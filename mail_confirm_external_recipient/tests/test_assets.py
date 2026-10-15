from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAssets(TransactionCase):
    def test_backend_bundle_contains_patches(self):
        paths = [
            asset[0]
            for asset in self.env["ir.asset"]._get_asset_paths("web.assets_backend", {})
        ]
        for path in (
            "/mail_confirm_external_recipient/static/src/core/common/composer_patch.js",
            "/mail_confirm_external_recipient/static/src/chatter/web/"
            "mail_composer_send_dropdown_patch.js",
        ):
            self.assertIn(path, paths)
