# -*- coding: utf-8 -*-

from odoo import models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.multi
    def action_multi_picking_check_availibility(self):
        pickings = self.filtered(lambda x: x.show_check_availability)
        if pickings:
            pickings.action_assign()
    
    