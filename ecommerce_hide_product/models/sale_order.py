from odoo import models, _
import random

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_accessories(self):
        """ Suggest accessories based on 'Accessory Products' of products in cart """
        for order in self:
            products = order.website_order_line.mapped('product_id')
            products = products.filtered(lambda x: not x.hide_accessory_product)
            accessory_products = self.env['product.product']
            for line in order.website_order_line.filtered(lambda l: l.product_id and not l.product_id.hide_accessory_product):
                combination = line.product_id.product_template_attribute_value_ids + line.product_no_variant_attribute_value_ids
                accessory_products |= line.product_id.accessory_product_ids.filtered(lambda product:
                                                                                     product.website_published and
                                                                                     product not in products and
                                                                                     product._is_variant_possible(
                                                                                         parent_combination=combination)
                                                                                     )

            return random.sample(accessory_products, len(accessory_products))

