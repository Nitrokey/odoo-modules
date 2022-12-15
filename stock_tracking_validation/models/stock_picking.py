# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def open_stock_tracking_wizard(self):
        action = self.env.ref('stock_tracking_validation.action_product_stock_validation').read()[0]
        product_data = ''
        for produce_line in self.move_ids_without_package:
            name = produce_line.product_id.name
            lot = produce_line.active_move_line_ids.mapped('lot_id').name
            product_data += ''+name+': '+str(lot)+'\n'
        action['context'] = {'default_product_data': product_data}
        return action