import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.sale.controllers.product_configurator import ProductConfiguratorController
from odoo.exceptions import UserError


class ProductConfiguratorController(ProductConfiguratorController):

    def _show_optional_products(self, product_id, variant_values, pricelist, handle_stock, **kw):
        if kw.get('is_mandatory',False):
            add_qty = int(kw.get('add_qty', 1))
            product = request.env['product.product'].with_context(self._get_product_context(pricelist, **kw)).browse(int(product_id))
            to_currency = product.currency_id
    
            if pricelist:
                to_currency = pricelist.currency_id
    
            parent_combination = product.product_template_attribute_value_ids
            if product.env.context.get('no_variant_attribute_values'):
                # Add "no_variant" attribute values' exclusions
                # They are kept in the context since they are not linked to this product variant
                parent_combination |= product.env.context.get('no_variant_attribute_values')
    
            return request.env['ir.ui.view'].render_template("product_mandatory_products.mandatory_products_modal", {
                # product deprecated, it's not used in the view
                'product': product,
                # reference_product deprecated, use parent_combination instead
                'reference_product': product,
                'parent_combination': parent_combination,
                'pricelist': pricelist,
                # to_currency deprecated, get from pricelist or product
                'to_currency': to_currency,
                # get_attribute_exclusions deprecated, use product method
                'get_attribute_exclusions': self._get_attribute_exclusions,
                'add_qty': add_qty,
            })
        else:
            return super(ProductConfiguratorController,self)._show_optional_products(product_id, variant_values, pricelist, handle_stock, **kw)
       
    

class WebsiteSale(WebsiteSale):
    
    KW = {}
    
    @http.route(['/shop/cart/update_option'], type='http', auth="public", methods=['POST'], website=True, multilang=False)
    def cart_options_update_json(self, product_id, add_qty=1, set_qty=0, goto_shop=None, lang=None, goToShop=False, **kw):
        if goToShop == "true":
            kw.update(self.KW)
            res = super(WebsiteSale, self).cart_options_update_json(product_id, add_qty=add_qty, set_qty=set_qty,goto_shop=goto_shop,lang=lang, **kw)
            self.KW = {}
        else:
            self.KW.update(kw)
        return res

    @http.route(['/shop/check_mendatory_product'], type='json', auth='public')
    def check_mendatory_product(self, **product_data):
        if product_data.get('product_id')[0].get('product_id') or False:
            product_id = request.env['product.product'].sudo().browse(int(product_data.get('product_id')[0].get('product_id')))
            if product_id.mandatory_product_ids:
                
                add_cart_product_ids = [i.get('product_id') for i in product_data.get('product_id')]
                
                if any([l in add_cart_product_ids for l in product_id.mandatory_product_ids.mapped('product_variant_id').ids]):
                
                    return True
                else:
                    return False
            else:   
                return True
        else:
            return True
    
    
    @http.route(['/shop/is_mendatory_product'], type='json', auth='public')
    def is_mendatory_product(self, **product_data):
        print(product_data)
        if product_data.get('product_id'):
            product_id = request.env['product.product'].sudo().browse(int(product_data.get('product_id')))
            if product_id.mandatory_product_ids:
                return True
            else:
                return False
        else:
            return False
        
    