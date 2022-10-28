# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_count = fields.Integer(string='Delivery Count', compute='_compute_delivery_count')

    def _compute_delivery_count(self):
        delivery_obj = self.env['stock.picking']
        for partner in self:
            partner.delivery_count = delivery_obj.search_count([
                ('partner_id', '=', partner.id),
                ('picking_type_id.code', '=', 'outgoing'),
            ])

    #@api.multi
    def action_view_partner_delivery(self):
        delivery_orders = self.env['stock.picking'].search([
            ('partner_id', '=', self.id),
            ('picking_type_id.code', '=', 'outgoing'),
        ])
        delivery_tree_view = self.env.ref("stock.vpicktree")
        delivery_form_view = self.env.ref("stock.view_picking_form")
        return {
            'name': 'Transfers',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'views': [(delivery_tree_view.id, 'tree'), (delivery_form_view.id, 'form')],
            'domain': [('id', 'in', delivery_orders.ids)],
        }
