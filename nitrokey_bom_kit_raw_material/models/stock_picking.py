# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_generate_unbuild_order(self):
        mo_id = self.env['mrp.production'].search([
            ('sale_order_id', '=', self.sale_id.id)
        ], limit=1)
        quantity = self.move_ids_without_package[0].quantity_done
        unbuild_vals = {
            'mo_id': mo_id.id,
            'product_id': mo_id.product_id.id,
            'product_qty': quantity,
            'product_uom_id': mo_id.product_uom_id.id,
            'bom_id': mo_id.bom_id.id,
        }
        unbuild_order = self.env['mrp.unbuild'].create(unbuild_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unbuild Order'),
            'res_model': 'mrp.unbuild',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', '=', unbuild_order.id)],
        }
