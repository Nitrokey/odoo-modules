# -*- coding: utf-8 -*-

from odoo import api, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.multi
    def name_get(self):
        ctx = self._context.copy() or {}
        if ctx.get('only_show_customer_id') and 'show_address' not in ctx and 'show_address_only' not in ctx and 'show_email' not in ctx and 'html_format' not in ctx:
            res = []
            for record in self:
                res.append((record.id, str(record.id)))
            return res
        return super(ResPartner, self).name_get()
    