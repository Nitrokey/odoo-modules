# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class ProductConfigureController(http.Controller):
    
    @http.route(['/product_configure'], type='json', auth="user", methods=['POST'])
    def productconfigure(self, product_id, active_id, quantity, **kw):
        mrp_production = request.env['mrp.production'].browse(active_id)
        
        mrp_production.product_id = product_id
        mrp_production.onchange_product_id()
        mrp_production.product_qty = quantity
        mrp_production.move_raw_ids = False
        mrp_production._generate_moves()
        