# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pre_order_count = fields.Float('Pre-Order Count',
                                   compute='_compute_pre_order_count')

    def _compute_pre_order_count(self):
        move_obj = self.env['stock.move']
        for product_tmpl in self:
            stock_moves = move_obj.search([
                ('product_id.product_tmpl_id', '=', product_tmpl.id),
                ('picking_id', '!=', False),
                ('picking_id.picking_type_id.code', '=', 'outgoing'),
                ('picking_id.state', 'in', ['confirmed', 'assigned'])
            ])
            product_tmpl.pre_order_count = sum(stock_moves.mapped('product_uom_qty'))
        return True

    @api.multi
    def action_view_pre_order_moves(self):
        stock_moves = self.env['stock.move'].search([
            ('product_id.product_tmpl_id', '=', self.id),
            ('picking_id', '!=', False),
            ('picking_id.picking_type_id.code', '=', 'outgoing'),
            ('picking_id.state', 'in', ['confirmed', 'assigned'])
        ])
        return {
            'name': 'Pre-Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': self.env.ref("stock.view_move_tree").id,
            'domain': [('id', 'in', stock_moves.ids)],
        }
