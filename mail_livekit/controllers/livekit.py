from livekit.api import AccessToken, VideoGrants
from werkzeug.exceptions import NotFound

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools.misc import str2bool

from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context


class LivekitController(http.Controller):
    @http.route("/livekit/token", type="json", auth="public")
    @add_guest_to_context
    def livekit_token(self, channel_id):
        """Issue a LiveKit JWT token for the given Discuss channel.

        Minimal contract:
        - Input: channel_id
        - Output: {token, room_name, livekit_url}
        """
        channel_id = int(channel_id)
        channel = request.env["discuss.channel"].search(
            [("id", "=", channel_id)], limit=1
        )
        if not channel:
            raise NotFound()

        # Ensure the current persona (user or guest) is a channel member.
        # For public channels, this creates a member record for guests.
        member = channel._find_or_create_member_for_self()
        if not member:
            # Avoid leaking info about private channels.
            raise NotFound()

        icp = request.env["ir.config_parameter"].sudo()
        raw_enabled = icp.get_param("mail_livekit.livekit_enabled")
        livekit_enabled = str2bool(
            raw_enabled if isinstance(raw_enabled, str) else "False"
        )
        raw_livekit_url = icp.get_param("mail_livekit.livekit_server_url")
        raw_api_key = icp.get_param("mail_livekit.livekit_api_key")
        raw_api_secret = icp.get_param("mail_livekit.livekit_api_secret")

        livekit_url: str = ""
        api_key: str = ""
        api_secret: str = ""
        if isinstance(raw_livekit_url, str):
            livekit_url = raw_livekit_url
        if isinstance(raw_api_key, str):
            api_key = raw_api_key
        if isinstance(raw_api_secret, str):
            api_secret = raw_api_secret
        if not livekit_enabled:
            raise AccessError(_("LiveKit is not enabled"))

        if not (livekit_url and api_key and api_secret):
            raise AccessError(_("LiveKit is not configured"))

        partner, guest = request.env["res.partner"]._get_current_persona()
        if guest:
            participant_identity = f"guest_{guest.id}"
            participant_name = guest.name or "Guest"
        else:
            # For authenticated users we should always have a partner persona.
            participant_identity = f"partner_{request.env.user.partner_id.id}"
            participant_name = request.env.user.partner_id.name or request.env.user.name

        room_name = f"odoo_channel_{channel.id}"

        grants = VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )
        token = (
            AccessToken(str(api_key), str(api_secret))
            .with_identity(participant_identity)
            .with_name(participant_name)
            .with_grants(grants)
            .to_jwt()
        )

        return {
            "token": token,
            "room_name": room_name,
            "livekit_url": livekit_url,
        }
