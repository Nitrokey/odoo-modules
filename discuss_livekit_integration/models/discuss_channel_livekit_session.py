from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class DiscussChannelLivekitSession(models.Model):
    _name = "discuss.channel.livekit.session"
    _inherit = ["bus.listener.mixin"]
    _description = "Discuss LiveKit session"
    _rec_name = "channel_member_id"

    channel_member_id = fields.Many2one(
        "discuss.channel.member", required=True, ondelete="cascade", index=True
    )
    channel_id = fields.Many2one(
        "discuss.channel",
        related="channel_member_id.channel_id",
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner", related="channel_member_id.partner_id", string="Partner"
    )
    guest_id = fields.Many2one("mail.guest", related="channel_member_id.guest_id")

    write_date = fields.Datetime("Last Updated On", index=True)

    is_screen_sharing_on = fields.Boolean(string="Is sharing the screen")
    is_camera_on = fields.Boolean(string="Is sending user video")
    is_muted = fields.Boolean(string="Is microphone muted")
    is_deaf = fields.Boolean(string="Has disabled incoming sound")

    raising_hand = fields.Datetime(string="Raising hand")

    _sql_constraints = [
        (
            "channel_member_unique",
            "UNIQUE(channel_member_id)",
            "There can only be one livekit session per channel member",
        )
    ]

    def _bus_channel(self):
        return self.channel_member_id._bus_channel()

    def _to_payload(self, *, only_id=False):
        self.ensure_one()
        if only_id:
            return {"id": self.id}
        name = ""
        if self.partner_id:
            name = self.partner_id.name or ""
        elif self.guest_id:
            name = self.guest_id.name or "Guest"
        return {
            "id": self.id,
            "channelId": self.channel_id.id,
            "channelMemberId": self.channel_member_id.id,
            "partnerId": self.partner_id.id or False,
            "guestId": self.guest_id.id or False,
            "name": name,
            "isCameraOn": bool(self.is_camera_on),
            "isDeaf": bool(self.is_deaf),
            "isMuted": bool(self.is_muted),
            "isScreenSharingOn": bool(self.is_screen_sharing_on),
            "raisingHand": self.raising_hand,
        }

    def _broadcast(self, action, sessions, *, only_id=False):
        """Broadcast session changes to channel members."""
        sessions = sessions.exists()
        if not sessions:
            return
        by_channel = {}
        for session in sessions:
            by_channel.setdefault(session.channel_id, []).append(session)
        for channel, channel_sessions in by_channel.items():
            # Use the channel "members" subchannel so that all members receive
            # the notification.
            channel._bus_send(
                "discuss.channel.livekit.session/update",
                {
                    "channelId": channel.id,
                    "action": action,
                    "sessions": [
                        s._to_payload(only_id=only_id) for s in channel_sessions
                    ],
                },
                subchannel="members",
            )

    @api.model_create_multi
    def create(self, vals_list):
        sessions = super().create(vals_list)
        sessions._broadcast("ADD", sessions)
        return sessions

    def unlink(self):
        sessions = self.exists()
        self._broadcast("DELETE", sessions, only_id=True)
        # send to channel members so other tabs can react.
        for session in sessions:
            session.channel_id._bus_send(
                "discuss.channel.livekit.session/ended",
                {"sessionId": session.id, "channelId": session.channel_id.id},
                subchannel="members",
            )
        return super().unlink()

    def _update_and_broadcast(self, values):
        valid_values = {
            "is_screen_sharing_on",
            "is_camera_on",
            "is_muted",
            "is_deaf",
            "raising_hand",
        }
        self.write({k: values[k] for k in valid_values if k in values})
        self._broadcast("UPDATE", self)

    @api.autovacuum
    def _gc_inactive_sessions(self):
        self.search(self._inactive_domain()).unlink()

    @api.model
    def _inactive_domain(self):
        return [
            (
                "write_date",
                "<",
                fields.Datetime.now() - relativedelta(minutes=1, seconds=15),
            )
        ]
