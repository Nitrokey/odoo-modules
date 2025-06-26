from odoo import fields, models, api
import uuid


class ResUsers(models.Model):
    _inherit = "res.users"

    firebase_token = fields.Char(help="Firebase device token for push notifications")
    firebase_notifications_enabled = fields.Boolean(
        string="Enable Firebase Notifications",
        default=False,
        help="Enable Firebase push notifications for chat and inbox messages",
    )

    @api.model
    def write(self, vals):
        """Auto-generate a test token when notifications are enabled"""
        result = super().write(vals)
        
        # If enabling notifications and no token exists, generate a test token
        if vals.get('firebase_notifications_enabled') and not self.firebase_token:
            test_token = f"test-token-{self.id}-{uuid.uuid4().hex[:8]}"
            super().write({'firebase_token': test_token})
            
        return result
