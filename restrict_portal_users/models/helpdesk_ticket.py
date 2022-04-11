from odoo import models, api


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.multi
    @api.onchange('team_id', 'user_id')
    def _onchange_dominion_user_id(self):
        if self.user_id:
            if self.user_id and self.user_ids and \
                    self.user_id not in self.user_ids:
                self.update({
                    'user_id': False
                })
                return {'domain': {'user_id': []}}
        if self.team_id:
            return {'domain': {'user_id': [('share', '=', False), ('id', 'in', self.user_ids.ids)]}}
        else:
            return {'domain': {'user_id': [('share', '=', False)]}}
