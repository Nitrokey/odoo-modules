from odoo import fields, models, api
from odoo.exceptions import UserError
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

    def action_enable_firebase_notifications(self):
        """Action to enable Firebase notifications with JavaScript integration"""
        self.ensure_one()
        
        # Return a client action that executes JavaScript
        return {
            'type': 'ir.actions.client',
            'tag': 'firebase_enable_notifications',
            'context': {
                'user_id': self.id,
            }
        }

    def action_test_firebase_notification(self):
        """Action to send a test Firebase notification"""
        self.ensure_one()
        
        if not self.firebase_notifications_enabled or not self.firebase_token:
            raise UserError("Firebase notifications are not enabled or no token is registered. Please enable notifications first.")
        
        # Try to send test notification via Firebase tools
        try:
            firebase_tools = self.env['firebase.tools']
            result = firebase_tools.send_notification(
                self.firebase_token,
                'Test Notification',
                'This is a test notification from Odoo Firebase integration!',
                {
                    'test': True,
                    'user_id': self.id,
                    'timestamp': str(self.env.cr.now())
                }
            )
            
            if result:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Test notification sent successfully!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError("Failed to send test notification")
                
        except Exception as e:
            raise UserError(f"Failed to send test notification: {str(e)}")
