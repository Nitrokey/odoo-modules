import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MessageExternalUserController(http.Controller):
    @http.route("/message/external_users/check", type="json", auth="user", csrf=False)
    def check_external_users(self, rec_id=None, model=None):
        """To check for external users exist in record followers"""
        try:
            if not rec_id or not model:
                return False

            record = request.env[model].browse(rec_id)
            followers = record.message_follower_ids

            for follower in followers:
                partner = follower.partner_id

                # If partner has no users at all, they're external
                if not partner.user_ids:
                    return True

                # Check if any user is not internal
                for user in partner.user_ids:
                    if not user.has_group("base.group_user"):
                        return True

            return False

        except Exception as e:
            _logger.error("Error checking external users: %s", str(e))
            return False
