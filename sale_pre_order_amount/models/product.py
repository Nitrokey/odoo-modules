# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pre_order_count = fields.Integer(string='Pre-Order Count', compute='_compute_pre_order_count')

    def _compute_pre_order_count(self):
        product_obj = self.env['product.product']
        move_obj = self.env['stock.move']
        for product in self:
            move_product = product_obj.search([('product_tmpl_id', '=', product.id)])
            stock_moves = move_obj.search([
                ('product_id', '=', move_product.id),
                ('picking_id', '!=', False),
                ('picking_id.picking_type_id.code', '=', 'outgoing'),
                ('picking_id.state', 'in', ['confirmed', 'assigned'])
            ])
            product.pre_order_count = sum(stock_moves.mapped('product_uom_qty'))

    @api.multi
    def action_view_pre_order_moves(self):
        move_product = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        stock_moves = self.env['stock.move'].search([
            ('product_id', '=', move_product.id),
            ('picking_id', '!=', False),
            ('picking_id.picking_type_id.code', '=', 'outgoing'),
            ('picking_id.state', 'in', ['confirmed', 'assigned'])
        ])
        move_tree_view = self.env.ref("stock.view_move_tree")
        return {
            'name': 'Amount of Pre-Order',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': move_tree_view.id,
            'domain': [('id', 'in', stock_moves.ids)],
        }

