# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def open_stock_tracking_wizard(self):
        action = self.env.ref('stock_tracking_validation.action_product_stock_validation').read()[0]
        product_data = ''
        for produce_line in self.produce_line_ids:
            name = produce_line.product_id.name
            lot = produce_line.lot_id.name
            product_data += ''+name+': '+str(lot)+'\n'
        action['context'] = {'default_product_data': product_data}
        return action