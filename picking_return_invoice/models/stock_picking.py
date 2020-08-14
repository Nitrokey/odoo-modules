# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockOperationType(models.Model):
    _inherit = 'stock.picking.type'

    return_type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase')
    ], string='Return Type')


class StockPicking(models.Model):
    _inherit = "stock.picking"

    return_type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase')
    ], string='Return Type', related='picking_type_id.return_type', readonly=True, store=True)
    invoice_id = fields.Many2one('account.invoice', string="Invoice")

    def action_view_return_invoice(self):
        if self.return_type =='sale':
            action = self.env.ref('account.action_invoice_out_refund').read()[0]
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        else:
            action = self.env.ref('account.action_invoice_in_refund').read()[0]
            action['views'] = [(self.env.ref('account.invoice_supplier_form').id, 'form')]
        action['res_id'] = self.invoice_id.id
        return action

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        if self.state == 'draft' and self.return_type:
            if self.return_type == 'sale':
                self.location_dest_id = self.picking_type_id.default_location_dest_id
            if self.return_type == 'purchase':
                self.location_id = self.picking_type_id.default_location_src_id
        return res

    @api.multi
    def create_refund_invoice(self):
        inv_obj = self.env['account.invoice']
        for pick in self.filtered(lambda x:x.return_type):
            type = 'in_refund' if pick.return_type == 'purchase' else 'out_refund'
            inv_lines = {'type':type, 'partner_id':pick.partner_id.id, 'invoice_line_ids':[]}
            account = pick.return_type == 'sale' and pick.partner_id.property_account_receivable_id.id or pick.partner_id.property_account_payable_id.id
            inv_lines['account_id'] = account
            inv_lines['origin'] = pick.name
            inv_lines['name'] = pick.origin
            for line in pick.move_lines:
                name = line.product_id.partner_ref
                pricelist_id = pick.partner_id.property_product_pricelist
                price = pricelist_id.get_product_price(line.product_id, 1, pick.partner_id) if pricelist_id else line.product_id.lst_price
                inv_lines['invoice_line_ids'] += [(0, None, {'product_id':line.product_id.id,
                                       'name':name,
                                       'quantity':line.quantity_done,
                                       'price_unit': price,
                                       'account_id':line.product_id.product_tmpl_id.get_product_accounts()['income'].id})]
            if inv_lines['invoice_line_ids']:
                inv_id = inv_obj.create(inv_lines)
                pick.invoice_id = inv_id.id

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        self.create_refund_invoice()
        return res
