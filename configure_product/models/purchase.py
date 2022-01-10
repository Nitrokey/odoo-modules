from odoo import models, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if 'default_product_qty' in self._context and 'default_product_uom_qty' in self._context:
            self = self.with_context(configure_product_quantity=True)
        return super(PurchaseOrderLine, self).onchange_product_id()
    
    def _suggest_quantity(self):
        res = super(PurchaseOrderLine, self)._suggest_quantity()
        if self._context.get('configure_product_quantity') and self._context.get('default_product_qty'):
            self.product_qty = self._context.get('default_product_qty')
        return res
    