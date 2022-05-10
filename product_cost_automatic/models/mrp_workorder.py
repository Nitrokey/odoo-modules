# -*- coding: utf-8 -*-

from odoo import models, api

class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"
    
    def button_start(self):
        res = super(MrpWorkorder, self).button_start()
        if self.product_id.is_automatically:
            products = self.product_id
            bom = self.env['mrp.bom']._bom_find(products)[self]
            self.product_id.write({'standard_price':self.product_id._compute_bom_price(bom)}) 
        return res
