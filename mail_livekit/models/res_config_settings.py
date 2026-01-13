from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    livekit_enabled = fields.Boolean(
        string="Enable LiveKit",
        config_parameter="mail_livekit.livekit_enabled",
    )

    livekit_api_key = fields.Char(
        string="LiveKit API Key",
        config_parameter="mail_livekit.livekit_api_key",
    )
    livekit_api_secret = fields.Char(
        string="LiveKit API Secret",
        config_parameter="mail_livekit.livekit_api_secret",
    )
    livekit_server_url = fields.Char(
        string="LiveKit Server URL",
        config_parameter="mail_livekit.livekit_server_url",
    )
