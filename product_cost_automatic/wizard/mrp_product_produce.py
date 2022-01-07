# -*- coding: utf-8 -*-

from odoo import models, api

class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"
    
    @api.multi
    def do_produce(self):
        res = super(MrpProductProduce, self).do_produce()
        if self.product_id.is_automatically:
            self.product_id.write({'standard_price':self.product_id._get_price_from_bom()}) 
        return res