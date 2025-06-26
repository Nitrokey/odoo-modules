import base64
import json

from odoo import api, fields, models


class FirebaseConfig(models.Model):
    _name = "firebase.config"
    _description = "Firebase Configuration"
    _rec_name = "name"

    name = fields.Char(
        string="Configuration Name", default="Firebase Settings", required=True
    )
    private_key_file = fields.Binary(string="Firebase Private Key File", required=True)
    private_key_filename = fields.Char(string="Filename")
    is_active = fields.Boolean(string="Active", default=True)

    @api.model
    def get_firebase_credentials(self):
        """Get the active Firebase credentials"""
        config = self.search([("is_active", "=", True)], limit=1)
        if not config or not config.private_key_file:
            return None

        # Decode the binary file content
        private_key_content = base64.b64decode(config.private_key_file)

        # Parse JSON content
        try:
            credentials_dict = json.loads(private_key_content.decode("utf-8"))
            return credentials_dict
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    @api.model
    def create(self, vals):
        # Ensure only one active configuration exists
        if vals.get("is_active", False):
            self.search([("is_active", "=", True)]).write({"is_active": False})
        return super().create(vals)

    def write(self, vals):
        # Ensure only one active configuration exists
        if vals.get("is_active", False):
            self.search([("is_active", "=", True), ("id", "!=", self.id)]).write(
                {"is_active": False}
            )
        return super().write(vals)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    firebase_private_key_file = fields.Binary(
        help="Upload the Firebase service account private key JSON file",
    )
    firebase_private_key_filename = fields.Char()
    firebase_is_active = fields.Boolean(
        string="Enable Firebase Integration",
        default=False,
        help="Enable or disable Firebase integration",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        firebase_config = self.env["firebase.config"].search([], limit=1)
        if firebase_config:
            res.update(
                {
                    "firebase_private_key_file": firebase_config.private_key_file,
                    "firebase_private_key_filename": firebase_config.private_key_filename,
                    "firebase_is_active": firebase_config.is_active,
                }
            )
        return res

    def set_values(self):
        res = super().set_values()
        firebase_config = self.env["firebase.config"].search([], limit=1)

        if firebase_config:
            # Update existing configuration
            firebase_config.write(
                {
                    "private_key_file": self.firebase_private_key_file
                    or firebase_config.private_key_file,
                    "private_key_filename": self.firebase_private_key_filename
                    or firebase_config.private_key_filename,
                    "is_active": self.firebase_is_active,
                }
            )
        elif self.firebase_private_key_file:
            # Create new configuration only if file is provided
            self.env["firebase.config"].create(
                {
                    "name": "Firebase Settings",
                    "private_key_file": self.firebase_private_key_file,
                    "private_key_filename": self.firebase_private_key_filename,
                    "is_active": self.firebase_is_active,
                }
            )
        return res
