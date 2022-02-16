from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_automatically = fields.Boolean(
        'Automatic', compute='_compute_is_automatically',
        inverse='_set_is_automatically', store=True)
    
    @api.depends('product_variant_ids', 'product_variant_ids.is_automatically')
    def _compute_is_automatically(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.is_automatically = template.product_variant_ids.is_automatically
        for template in (self - unique_variants):
            template.is_automatically = False
            
    @api.one
    def _set_is_automatically(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.is_automatically = self.is_automatically
            
    def button_po_cost(self):
        return self.mapped('product_variant_ids').button_po_cost()
    
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    is_automatically = fields.Boolean(string='Automatically')
    
    
    def button_po_cost(self):
        for product in self:
            stock_id = self.env['stock.picking'].search([('state','=','done'),('purchase_id','!=',False),('move_ids_without_package.product_id','=',product.id)], order="id desc",limit=1)
            if stock_id.purchase_id:
                for po_l in stock_id.purchase_id.order_line:
                    if po_l.product_id == product:
                        product.standard_price = po_l.price_unit
            elif product.bom_count > 0:
                    product.standard_price = product._get_price_from_bom()
                
                        

    
                
