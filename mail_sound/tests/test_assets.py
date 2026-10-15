from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAssets(TransactionCase):
    def test_backend_bundle_contains_patch(self):
        paths = [
            asset[0]
            for asset in self.env["ir.asset"]._get_asset_paths("web.assets_backend", {})
        ]
        self.assertIn(
            "/mail_sound/static/src/services/out_of_focus_service_patch.js", paths
        )
