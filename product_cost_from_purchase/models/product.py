from odoo import fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    is_automatically = fields.Boolean(string='Automatically',default=True)
