from livekit.api import AccessToken, VideoGrants

from odoo import api, fields, models
from odoo.tools.misc import str2bool

from odoo.addons.mail.tools.discuss import Store


class MailRtcSession(models.Model):
    _inherit = "discuss.channel.rtc.session"

    livekit_token = fields.Char()
    livekit_room_name = fields.Char()
    livekit_url = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        livekit_params = self._get_livekit_config_params()

        result = super().create(vals_list)

        if not livekit_params.get("valid"):
            return

        for session in result:
            session._generate_livekit_token(livekit_params)

        return result

    def _get_livekit_config_params(self):
        icp = self.env["ir.config_parameter"].sudo()
        raw_enabled = icp.get_param("mail_livekit.livekit_enabled", False)
        livekit_enabled = str2bool(
            raw_enabled if isinstance(raw_enabled, str) else "False"
        )
        livekit_url = icp.get_param("mail_livekit.livekit_server_url")
        api_key = icp.get_param("mail_livekit.livekit_api_key")
        api_secret = icp.get_param("mail_livekit.livekit_api_secret")

        valid = (
            livekit_enabled
            and isinstance(livekit_url, str)
            and livekit_url.strip()
            and isinstance(api_key, str)
            and api_key.strip()
            and isinstance(api_secret, str)
            and api_secret.strip()
        )

        return {
            "valid": valid,
            "enabled": livekit_enabled,
            "url": livekit_url,
            "api_key": api_key,
            "api_secret": api_secret,
        }

    def _generate_livekit_token(self, livekit_params):
        self.ensure_one()
        room_name = f"odoo_channel_{self.channel_id.id}"
        grants = VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )

        name = (
            self.partner_id.name
            if self.partner_id
            else "Guest " + str(self.channel_member_id.id)
        )

        token = (
            AccessToken(livekit_params.get("api_key"), livekit_params.get("api_secret"))
            .with_identity(str(self.id))
            .with_name(name)
            .with_grants(grants)
            .to_jwt()
        )

        self.livekit_token = token
        self.livekit_room_name = room_name
        self.livekit_url = livekit_params.get("url")

    def _to_store(self, store: Store, extra=False):
        result = super()._to_store(store, extra)
        for rtc_session in self:
            if rtc_session.livekit_url:
                store.add(
                    rtc_session,
                    {
                        "livekit_token": rtc_session.livekit_token,
                        "livekit_room_name": rtc_session.livekit_room_name,
                        "livekit_url": rtc_session.livekit_url,
                    },
                )
        return result
