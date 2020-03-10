# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.multi
    @api.depends('refund_invoice_ids')
    def _compute_count_credit_note(self):
        for invoice in self:
            invoice.count_credit_note = len(invoice.refund_invoice_ids)
            
    count_credit_note = fields.Integer('Credit Note Count', compute='_compute_count_credit_note', store=True)
    
    @api.multi
    def action_button_credit_notes(self):
        invoices = self.mapped('refund_invoice_ids')
        action = self.env.ref('account.action_invoice_out_refund').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.invoice_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
