# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError


class ProductConfigureController(http.Controller):
    
    @http.route(['/product_configure'], type='json', auth="user", methods=['POST'])
    def productconfigure(self, product_id, active_id, quantity, **kw):
        mrp_production = request.env['mrp.production'].browse(active_id)
        if product_id:
            mrp_production.product_id = product_id
            mrp_production.onchange_product_id()
            mrp_production.product_qty = quantity
            mrp_production.move_raw_ids = False
            mrp_production._generate_moves()
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            action = request.env['ir.model.data'].xmlid_to_object('mrp.mrp_production_action')
            return base_url + '/web#id=%s&action=%s&model=mrp.production&view_type=form' % (mrp_production.id, action.id)
        raise ValidationError("Product does not found!!")
        