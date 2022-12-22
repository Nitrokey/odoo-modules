# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def check_users(self, follower_ids, rec_id, model):
        # partners = self.browse(partner_ids)
        followers=self.env['mail.followers']
        if follower_ids:
            followers = self.env['mail.followers'].browse(follower_ids)
        if rec_id and model:
            followers = self.env[model].browse(rec_id).message_follower_ids
        for follower in followers:
            for partner in follower.partner_id:
                if not partner.user_ids:
                    return True
                for user in partner.user_ids:
                    if user.has_group('base.group_portal'):
                        return True

        return False
