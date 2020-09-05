# -*- coding: utf-8 -*-
from odoo import models

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def rate_shipment(self, order):
        res = super(DeliveryCarrier, self).rate_shipment(order)
        del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_unregistered_grid_germany',False)
        method_matched = False
        if del_method and del_method.id == self.id:
            method_matched = True
        if not method_matched:
            del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_registered_grid_germany',False)
            if del_method and del_method.id == self.id:
                method_matched = True
        if not method_matched:
            del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_registered_grid_usa',False)
            if del_method and del_method.id == self.id:
                method_matched = True
        if not method_matched:
            del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_registered_grid_world',False)
            if del_method and del_method.id == self.id:
                method_matched = True
        if order.pricelist_id and method_matched:
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
