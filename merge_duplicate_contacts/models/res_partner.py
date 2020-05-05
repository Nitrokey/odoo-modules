# -*- coding: utf-8 -*-

from odoo import api, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.multi
    def name_get(self):
        if self._context.get('only_show_customer_id'):
            res = []
            for record in self:
                res.append((record.id, str(record.id)))
            return res
        return super(ResPartner, self).name_get()
    