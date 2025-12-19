import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MessageExternalUserController(http.Controller):
    @http.route("/message/external_users/check", type="json", auth="user")
    def check_external_users(self, rec_id, model, mentioned_partner_ids=None):
        """To check for external users exist in record followers"""
        confirmation_message = (
            "Your message will be sent to external partners (e.g. customers)."
        )
        # Check thread followers
        if not mentioned_partner_ids:
            record = request.env[model].browse(rec_id)
            followers = record.message_follower_ids
            for follower in followers:
                partner = follower.partner_id

                # If partner has no users at all, they're external
                if not partner.user_ids:
                    return {
                        "needs_confirmation": True,
                        "confirmation_message": confirmation_message,
                    }

                # Check if any user is not internal
                for user in partner.user_ids:
                    if not user.has_group("base.group_user"):
                        return {
                            "needs_confirmation": True,
                            "confirmation_message": confirmation_message,
                        }

        # Check mentioned partners
        if mentioned_partner_ids:
            partners = request.env["res.partner"].browse(mentioned_partner_ids).exists()

            for partner in partners:
                # If partner has no users at all, they're external
                if not partner.user_ids:
                    return {
                        "needs_confirmation": True,
                        "confirmation_message": confirmation_message,
                    }

                # Check if any user is not internal
                for user in partner.user_ids:
                    if not user.has_group("base.group_user"):
                        return {
                            "needs_confirmation": True,
                            "confirmation_message": confirmation_message,
                        }
        return {
            "needs_confirmation": False,
            "confirmation_message": "",
        }
