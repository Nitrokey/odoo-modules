# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.safe_eval import safe_eval

class SaleConfigSettings(models.TransientModel):
    _inherit='sale.config.settings'
    
    order_retention_period = fields.Integer("Order older than X hours", default=48, help='Retention period for order. Afer X hours order are deleted automatically.')
    max_delete_batch_limit = fields.Integer("Maximum record Delete limit", default=2000, help="User can delete maximum x records at a time.")
    
    @api.model
    def get_default_order_retention_period(self, fields):
        # we use safe_eval on the result, since the value of the parameter is a nonempty string
        return {
            'order_retention_period': safe_eval(self.env['ir.config_parameter'].get_param('abandoned_carts.order_retention_period', '48')),
            'max_delete_batch_limit': safe_eval(self.env['ir.config_parameter'].get_param('abandoned_carts.max_delete_batch_limit', '2000')),
        }
        
    @api.multi
    def set_order_retention_period(self):
        self.env['ir.config_parameter'].set_param('abandoned_carts.order_retention_period', repr(self.order_retention_period))
        self.env['ir.config_parameter'].set_param('abandoned_carts.max_delete_batch_limit', repr(self.max_delete_batch_limit))