from odoo import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(product_context)
        order_line = self.env['sale.order.line'].sudo()
        
        values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        # link a product to the sales order
        if kwargs.get('linked_line_id'):
            linked_line = SaleOrderLineSudo.browse(kwargs['linked_line_id'])
           
            if linked_line.product_id.mandatory_product_ids and order_line.browse(values.get('line_id')).product_id.id in linked_line.product_id.mandatory_product_ids.mapped('product_variant_id').ids:
                name = linked_line.name.split('\n')
                new_name = name[-1].replace('Option', _('Mandatory'))
                name.pop()
                name.append(new_name)
                linked_line.write({"name":'\n'.join(name)})
                if self._context.get('lang','')=='de_DE':
                    order_line.browse(values.get('line_id')).write({
                            'name': order_line.browse(values.get('line_id')).name.replace("Option für:","Verpflichtend für:"),
                        })
                else:
                    order_line.browse(values.get('line_id')).write({
                            'name': order_line.browse(values.get('line_id')).name.replace("Option for:","Mandatory for:"),
                        })    
            
        return values