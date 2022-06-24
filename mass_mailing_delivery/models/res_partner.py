from odoo import models, fields, api
from odoo.addons.mass_mailing.models.mass_mailing import MASS_MAILING_BUSINESS_MODELS

MASS_MAILING_BUSINESS_MODELS.append('stock.picking')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_count = fields.Integer(string='Delivery Count', compute='_compute_picking_ids',store=True)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sale Order Count',search='_search_sale_order_count')


    @api.depends('sale_order_ids')
    def _compute_picking_ids(self):
        for partner in self:
            count_picking = 0
            for delivery in partner.sale_order_ids:
                count_picking += len(delivery.picking_ids)
            partner.delivery_count += count_picking
     
    @api.multi
    def _search_sale_order_count(self, operator, value):
        _query = """select partner_id as order from sale_order group by partner_id having count(id) %s %d;""" % (operator, value)
        if not value:
            _query = """select partner_id as order from sale_order group by partner_id having count(id) > %d;""" % (value)
            
        self.env.cr.execute(_query )
        partners = self.env.cr.fetchall()
        if partners:
            partners = [item[0] for item in partners]
            if not value and operator == '=':
                return [('id', 'not in', partners)] 
        return [('id', 'in', partners)]
