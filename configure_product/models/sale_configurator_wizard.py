from odoo import models, api,_
from lxml import etree

from odoo.osv.orm import setup_modifiers

        
class SaleProductConfigurator(models.TransientModel):
    _inherit = 'sale.product.configurator'
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        context = self.env.context
        ctx = context.get('config_product')
        if view_type in ('form'):
            domain = "[('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), ('sale_ok', '=', True), '|', ('attribute_line_ids.value_ids', '!=', False), ('optional_product_ids', '!=', False)]"
            res = super(SaleProductConfigurator, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
            if ctx == True:
                doc = etree.XML(res['arch'])
                node = doc.xpath("//field[@name='product_template_id']")[0]
                node.set('domain', domain)
                setup_modifiers(node, None)
                res['arch'] = etree.tostring(doc)
            return res
        return super(SaleProductConfigurator, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        
        
       