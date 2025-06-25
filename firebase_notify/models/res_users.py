from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    firebase_token = fields.Char(help="Firebase device token for push notifications")
    firebase_notifications_enabled = fields.Boolean(
        string="Enable Firebase Notifications",
        default=False,
        help="Enable Firebase push notifications for chat and inbox messages",
    )
