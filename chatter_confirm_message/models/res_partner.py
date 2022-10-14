from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def check_users(self, rec_id, model):
        followers = self.env["mail.followers"]
        if rec_id and model:
            followers = self.env[model].browse(rec_id).message_follower_ids
        for follower in followers:
            for partner in follower.partner_id:
                if not partner.user_ids:
                    return True
                for user in partner.user_ids:
                    if user.has_group("base.group_portal"):
                        return True

        return False
