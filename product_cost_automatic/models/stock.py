from odoo import models, api

class Picking(models.Model):
    _inherit = "stock.picking"
    
    @api.multi
    def action_done(self):
        res = super(Picking, self).action_done()
        if res:
            for purchase in self.mapped('purchase_id'):
                for line in purchase.order_line:
                    if line.product_id.is_automatically or line.product_id.product_tmpl_id.is_automatically:
                        line.product_id.write({'standard_price':line.price_unit or 0.0})
        return res