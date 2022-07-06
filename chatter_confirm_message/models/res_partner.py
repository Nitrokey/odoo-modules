import re

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def check_users(self, follower_ids):
        mail = []
        for i in follower_ids:

            str_id = re.search(r"\d+", i)
            mail.append(int(str_id.group()))

        followers = self.env["mail.followers"].browse(mail)
        for follower in followers:
            for partner in follower.partner_id:
                if not partner.user_ids:
                    return True
                for user in partner.user_ids:
                    if user.has_group("base.group_portal"):
                        return True

        return False
