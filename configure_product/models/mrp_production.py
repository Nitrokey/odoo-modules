from odoo import models

class MRPProduction(models.Model):
    _inherit = 'mrp.production'
    
    def product_config_wizard(self):
        form_view = self.env.ref('sale.sale_product_configurator_view_form')
        return {
            'name': 'Configure a product',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.product.configurator',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(form_view.id, 'form')],
            'target': 'new',
            'context': {'config_product': True},
        }
        
