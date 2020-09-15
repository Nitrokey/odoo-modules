# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    is_free_for_promotion = fields.Boolean('Is Free for Promotion')
    
    @api.model
    def _setup_free_delivery_methods(self):
        del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_unregistered_grid_germany',False)
        delivery_methods = self.browse()
        if del_method:
            delivery_methods += del_method
        del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_registered_grid_germany',False)
        if del_method:
            delivery_methods += del_method
            
        del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_registered_grid_usa',False)
        if del_method:
            delivery_methods += del_method
            
        del_method = self.sudo().env.ref('nitrokey_delivery_setup.carrier_letter_registered_grid_world',False)
        if del_method:
            delivery_methods += del_method
            
        if len(delivery_methods):
            delivery_methods.write({'is_free_for_promotion' : True})
                
    def rate_shipment(self, order):
        res = super(DeliveryCarrier, self).rate_shipment(order)
        
        if order.pricelist_id and self.is_free_for_promotion:
            
            free_ship = True
            
            for line in order.order_line:
                if line.is_delivery:
                    continue
                quantity=line.product_uom_qty
                partner=line.order_id.partner_id
                
                for product_id, item_rule in order.pricelist_id.get_price_rule_for_free_shipment([(line.product_id, quantity, partner)]).items():
                    if not item_rule or not item_rule.free_shipment:
                        free_ship = False
                        break
                if not free_ship:
                    break
            if free_ship:
                res.update({'price': 0.0})
        return res
