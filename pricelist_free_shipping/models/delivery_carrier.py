# -*- coding: utf-8 -*-
from odoo import api, fields, models

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def rate_shipment(self, order):
        res = super(DeliveryCarrier, self).rate_shipment(order)
        if order.pricelist_id:
            free_ship = True
            for product in [line.product_id for line in order.order_line.filtered(lambda x: not x.is_delivery)]:
                item = self.env['product.pricelist.item'].search([('product_tmpl_id','=', product.product_tmpl_id.id), ('pricelist_id', '=', order.pricelist_id.id)], limit = 1)
                if not item:
                    item = self.env['product.pricelist.item'].search([('product_id','=', product.id), ('pricelist_id', '=', order.pricelist_id.id)], limit = 1)
                if not item.free_shipment:
                    free_ship = False
        if free_ship:
            res.update({'price': 0.0})
        return res
