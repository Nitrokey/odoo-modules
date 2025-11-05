from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def check_users(self, rec_id, model):
        followers = self.env["mail.followers"]
        if rec_id and model:
            followers = self.env[model].browse(rec_id).message_follower_ids

        for follower in followers:
            partner = follower.partner_id
            if not partner.user_ids:
                # Partners without users are external
                return True

            # Check if partner has any non-internal users
            for user in partner.user_ids:
                if not user.has_group("base.group_user"):
                    # User is not an internal user (could be portal, public, or other)
                    return True

        return False
