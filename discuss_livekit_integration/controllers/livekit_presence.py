import logging

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context

_logger = logging.getLogger(__name__)


def _coerce_bool(value, *, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "t", "yes", "y", "on"):
            return True
        if v in ("0", "false", "f", "no", "n", "off"):
            return False
    return bool(default)


class LivekitPresenceController(http.Controller):
    @http.route(
        "/mail/livekit/channel/join_call", methods=["POST"], type="json", auth="public"
    )
    @add_guest_to_context
    def join_call(self, channel_id, camera=False):
        try:
            channel_id = int(channel_id)
        except Exception:
            raise NotFound() from None
        channel = request.env["discuss.channel"].search([("id", "=", channel_id)])
        if not channel:
            raise request.not_found()
        member = channel._find_or_create_member_for_self()
        if not member:
            raise NotFound()

        camera = _coerce_bool(camera, default=False)

        session_sudo = (
            request.env["discuss.channel.livekit.session"]
            .sudo()
            .search([("channel_member_id", "=", member.id)], limit=1)
        )
        if not session_sudo:
            session_sudo = (
                request.env["discuss.channel.livekit.session"]
                .sudo()
                .create(
                    {
                        "channel_member_id": member.id,
                        "is_camera_on": camera,
                    }
                )
            )

            # Mimic base RTC semantics: when the first participant starts a
            # call in a non-channel thread, ring other connected members.
            try:
                session_count = (
                    request.env["discuss.channel.livekit.session"]
                    .sudo()
                    .search_count([("channel_id", "=", channel.id)])
                )
                if session_count == 1 and channel.channel_type != "channel":
                    channel._bus_send(
                        "discuss.channel.livekit.call/invitation",
                        {
                            "channelId": channel.id,
                            "inviterSessionId": session_sudo.id,
                        },
                        subchannel="members",
                    )
            except Exception:
                # Best-effort: invitations are optional; presence still works.
                _logger.exception("LiveKit invitation broadcast failed")
        else:
            # If the session already exists (e.g., tab reload), broadcast an
            # UPDATE so other participants still get an immediate presence signal.
            session_sudo._update_and_broadcast({"is_camera_on": camera})

        # Return minimal presence info; frontend will still obtain LiveKit token
        # via /livekit/token.
        sessions = (
            request.env["discuss.channel.livekit.session"]
            .sudo()
            .search([("channel_id", "=", channel.id)])
        )
        return {
            "selfSessionId": session_sudo.id,
            "channelId": channel.id,
            "sessions": [s._to_payload() for s in sessions],
        }

    @http.route(
        "/mail/livekit/channel/leave_call", methods=["POST"], type="json", auth="public"
    )
    @add_guest_to_context
    def leave_call(self, channel_id):
        try:
            channel_id = int(channel_id)
        except Exception:
            raise NotFound() from None
        member = request.env["discuss.channel.member"].search(
            [("channel_id", "=", channel_id), ("is_self", "=", True)], limit=1
        )
        if not member:
            raise NotFound()
        session_sudo = (
            request.env["discuss.channel.livekit.session"]
            .sudo()
            .search([("channel_member_id", "=", member.id)], limit=1)
        )
        if session_sudo:
            session_sudo.unlink()

    @http.route(
        "/mail/livekit/session/update_and_broadcast",
        methods=["POST"],
        type="json",
        auth="public",
    )
    @add_guest_to_context
    def update_and_broadcast(self, session_id, values):
        # Match Odoo RTC semantics: only the owning persona can update its session.
        try:
            session_id = int(session_id)
        except Exception:
            return
        if not isinstance(values, dict):
            return
        session_sudo = (
            request.env["discuss.channel.livekit.session"]
            .sudo()
            .browse(session_id)
            .exists()
        )
        if not session_sudo:
            return

        if request.env.user._is_public():
            guest = request.env["mail.guest"]._get_guest_from_context()
            if not guest or session_sudo.guest_id != guest:
                return
        else:
            if session_sudo.partner_id != request.env.user.partner_id:
                return

        session_sudo._update_and_broadcast(values)

    @http.route(
        "/discuss/livekit/channel/ping", methods=["POST"], type="json", auth="public"
    )
    @add_guest_to_context
    def ping(self, channel_id, livekit_session_id=None, check_session_ids=None):
        try:
            channel_id = int(channel_id)
        except Exception:
            raise NotFound() from None
        member = request.env["discuss.channel.member"].search(
            [("channel_id", "=", channel_id), ("is_self", "=", True)], limit=1
        )
        if not member:
            raise NotFound()

        if livekit_session_id:
            try:
                livekit_session_id = int(livekit_session_id)
            except Exception:
                livekit_session_id = None
            session = (
                request.env["discuss.channel.livekit.session"]
                .sudo()
                .browse(livekit_session_id)
                .exists()
                if livekit_session_id
                else request.env["discuss.channel.livekit.session"]
            )
            if session and session.channel_member_id.id == member.id:
                session.write({})

        current_sessions = (
            request.env["discuss.channel.livekit.session"]
            .sudo()
            .search([("channel_id", "=", channel_id)])
        )
        current_ids = set(current_sessions.ids)
        outdated_ids = []
        if isinstance(check_session_ids, list | tuple):
            for sid in check_session_ids:
                try:
                    sid = int(sid)
                except Exception:
                    continue
                if sid not in current_ids:
                    outdated_ids.append(sid)

        return {
            "channelId": channel_id,
            "sessions": [s._to_payload() for s in current_sessions],
            "outdatedSessionIds": outdated_ids,
        }
