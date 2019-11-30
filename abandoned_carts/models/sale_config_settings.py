# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.safe_eval import safe_eval

class SaleConfigSettings(models.TransientModel):
    _inherit='sale.config.settings'
    
    order_retention_period = fields.Integer("Order older than X days", help='Retention period for order. Afer X days order are deleted automatically.')
    
    @api.model
    def get_default_order_retention_period(self, fields):
        # we use safe_eval on the result, since the value of the parameter is a nonempty string
        return {
            'order_retention_period': safe_eval(self.env['ir.config_parameter'].get_param('abandoned_carts.order_retention_period', '0')),
        }
        
    @api.multi
    def set_order_retention_period(self):
        self.env['ir.config_parameter'].set_param('abandoned_carts.order_retention_period', repr(self.order_retention_period))
        