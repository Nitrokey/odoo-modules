from odoo import fields, models,api
from lxml import etree

from odoo.osv.orm import setup_modifiers


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_automatically = fields.Boolean(string='Automatically',default=True)

    
    def button_po_cost(self):
        return self.mapped('product_variant_ids').button_po_cost()
               
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductTemplate, self).fields_view_get(view_id, view_type, toolbar, submenu)
        if res.get('model') == "product.template":
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='is_automatically']"):
                node.set('invisible', "[('product_variant_count', '&gt;', 1),('is_product_variant', '=', False)]")
                setup_modifiers(node, None)
            res['arch'] = etree.tostring(doc)
        return res
    
    

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    is_automatically = fields.Boolean(string='Automatically',default=True)
    
    
    def button_po_cost(self):
        for product in self:
            stock_id = self.env['stock.picking'].search([('state','=','done'),('purchase_id','!=',False),('move_ids_without_package.product_id','=',product.id)], order="id desc",limit=1)
            if stock_id.purchase_id:
                for po_l in stock_id.purchase_id.order_line:
                    if po_l.product_id == product:
                        product.standard_price = po_l.price_unit
            elif product.bom_count > 0:
                    product.standard_price = product._get_price_from_bom()
                
                        

    
                
