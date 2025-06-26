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
    
    # Web App Configuration (for client-side Firebase SDK)
    web_api_key = fields.Char(string="Web API Key", help="Firebase Web API Key")
    web_auth_domain = fields.Char(string="Auth Domain", help="Firebase Auth Domain (project-id.firebaseapp.com)")
    web_project_id = fields.Char(string="Project ID", help="Firebase Project ID")
    web_storage_bucket = fields.Char(string="Storage Bucket", help="Firebase Storage Bucket")
    web_messaging_sender_id = fields.Char(string="Messaging Sender ID", help="Firebase Cloud Messaging Sender ID")
    web_app_id = fields.Char(string="App ID", help="Firebase Web App ID")
    vapid_key = fields.Char(string="VAPID Key", help="Firebase Web Push VAPID Key")

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
    
    # Web App Configuration fields
    firebase_web_api_key = fields.Char(string="Web API Key", help="Firebase Web API Key")
    firebase_web_auth_domain = fields.Char(string="Auth Domain", help="Firebase Auth Domain (project-id.firebaseapp.com)")
    firebase_web_project_id = fields.Char(string="Project ID", help="Firebase Project ID")
    firebase_web_storage_bucket = fields.Char(string="Storage Bucket", help="Firebase Storage Bucket")
    firebase_web_messaging_sender_id = fields.Char(string="Messaging Sender ID", help="Firebase Cloud Messaging Sender ID")
    firebase_web_app_id = fields.Char(string="App ID", help="Firebase Web App ID")
    firebase_vapid_key = fields.Char(string="VAPID Key", help="Firebase Web Push VAPID Key")

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
                    "firebase_web_api_key": firebase_config.web_api_key,
                    "firebase_web_auth_domain": firebase_config.web_auth_domain,
                    "firebase_web_project_id": firebase_config.web_project_id,
                    "firebase_web_storage_bucket": firebase_config.web_storage_bucket,
                    "firebase_web_messaging_sender_id": firebase_config.web_messaging_sender_id,
                    "firebase_web_app_id": firebase_config.web_app_id,
                    "firebase_vapid_key": firebase_config.vapid_key,
                }
            )
        return res

    def set_values(self):
        res = super().set_values()
        firebase_config = self.env["firebase.config"].search([], limit=1)

        values_to_update = {
            "is_active": self.firebase_is_active,
            "web_api_key": self.firebase_web_api_key,
            "web_auth_domain": self.firebase_web_auth_domain,
            "web_project_id": self.firebase_web_project_id,
            "web_storage_bucket": self.firebase_web_storage_bucket,
            "web_messaging_sender_id": self.firebase_web_messaging_sender_id,
            "web_app_id": self.firebase_web_app_id,
            "vapid_key": self.firebase_vapid_key,
        }

        if self.firebase_private_key_file:
            values_to_update.update({
                "private_key_file": self.firebase_private_key_file,
                "private_key_filename": self.firebase_private_key_filename,
            })

        if firebase_config:
            # Update existing configuration
            firebase_config.write(values_to_update)
        elif self.firebase_private_key_file:
            # Create new configuration only if file is provided
            values_to_update.update({
                "name": "Firebase Settings",
                "private_key_file": self.firebase_private_key_file,
                "private_key_filename": self.firebase_private_key_filename,
            })
            self.env["firebase.config"].create(values_to_update)
        return res
