import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to send Firebase notifications for new messages"""
        messages = super().create(vals_list)

        for message in messages:
            self._send_firebase_notification(message)

        return messages

    def _send_firebase_notification(self, message):
        """Send Firebase notification for a message"""
        try:
            # Only send notifications for certain message types
            if message.message_type not in ["comment", "notification"]:
                return

            # Get recipients who should receive notifications
            recipients = self._get_notification_recipients(message)

            if not recipients:
                return

            # Prepare notification messages
            notification_messages = []
            for recipient in recipients:
                if (
                    recipient.firebase_notifications_enabled
                    and recipient.firebase_token
                ):
                    notification_messages.append(
                        {
                            "token": recipient.firebase_token,
                            "title": self._get_notification_title(message),
                            "body": self._get_notification_body(message),
                        }
                    )

            if notification_messages:
                # Import and send Firebase notifications
                from odoo.addons.firebase_integration.tools.firebase import (
                    send_firebase_notifications,
                )

                success_count = send_firebase_notifications(
                    notification_messages, self.env
                )
                _logger.info(
                    f"Sent {success_count} Firebase notifications for message {message.id}"
                )

        except Exception as e:
            _logger.error(
                f"Failed to send Firebase notification for message {message.id}: {str(e)}"
            )

    def _get_notification_recipients(self, message):
        """Get users who should receive Firebase notifications for this message"""
        recipients = self.env["res.users"]

        # For messages with specific partner recipients
        if message.partner_ids:
            recipients = message.partner_ids.mapped("user_ids").filtered(
                lambda u: u.firebase_notifications_enabled and u.firebase_token
            )

        # For channel messages, get channel members
        elif hasattr(message, "channel_ids") and message.channel_ids:
            for channel in message.channel_ids:
                if hasattr(channel, "channel_partner_ids"):
                    channel_users = channel.channel_partner_ids.mapped(
                        "user_ids"
                    ).filtered(
                        lambda u: u.firebase_notifications_enabled and u.firebase_token
                    )
                    recipients |= channel_users

        # Exclude the message author
        if message.author_id and message.author_id.user_ids:
            recipients -= message.author_id.user_ids

        return recipients

    def _get_notification_title(self, message):
        """Get notification title based on message context"""
        if message.model and message.res_id:
            try:
                record = self.env[message.model].browse(message.res_id)
                if hasattr(record, "display_name"):
                    return f"New message in {record.display_name}"
            except Exception as e:
                _logger.debug(
                    f"Could not get display_name for {message.model} "
                    f"record {message.res_id}: {e}"
                )

        if message.subject:
            return f"New message: {message.subject}"

        return "New message"

    def _get_notification_body(self, message):
        """Get notification body from message content"""
        if message.author_id:
            author_name = message.author_id.name
        else:
            author_name = "Someone"

        # Get plain text content (strip HTML)
        body = message.body or ""
        if body:
            # Simple HTML stripping (for basic cases)
            import re

            body = re.sub("<[^<]+?>", "", body)
            body = body.strip()

            # Limit body length
            if len(body) > 100:
                body = body[:97] + "..."

        if body:
            return f"{author_name}: {body}"
        else:
            return f"{author_name} sent a message"
