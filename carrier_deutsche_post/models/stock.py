# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
#import time


class Picking(models.Model):
    _inherit = 'stock.picking'

    label_de_attach_id = fields.Many2one('ir.attachment', 'Label Deutsche Post', copy=False)
    carrier_type = fields.Selection(related='carrier_id.type', string='Deutsche Post Carrier Type', readonly=True)

    @api.multi
    def get_deutsche_post_label(self):
        self.ensure_one()

        if self.label_de_attach_id:
            return {
                'type': 'ir.actions.act_url',
                'url': "/web/content/?model=ir.attachment&id=" + str(self.label_de_attach_id.id) + "&field=datas&download=true&filename_field=name",
                'target': 'download',
            }

        carrier_acc = False
        product_code = False
        if self.carrier_id.carrier_account_id:
            carrier_acc = self.carrier_id.carrier_account_id
            product_code = self.carrier_id.product_code
#         else:
#             grid_id = self.carrier_id.grid_get(contact_id=self.partner_id.id)
#             if grid_id:
#                 grid = self.env['delivery.grid'].browse(grid_id)
#                 carrier_acc = grid.carrier_account_id
#                 product_code = grid.product_code

        if not carrier_acc or carrier_acc.type != 'deutsche_post':
            raise Warning(_('There is not any Deutsche post account associated with the delivery method'))

        if not product_code:
            raise Warning(_('Please configure Product Code along with Carrier account in Carrier or Grid configuration'))

        data = {
            'name': self.name,
            'prod_code': product_code,
            'dest': {
                'first': '',
                'last': self.partner_id.name,
                'street': self.partner_id.street or '',
                'street2': self.partner_id.street2 or '',
                'zip': self.partner_id.zip or '',
                'city': self.partner_id.city or '',
                'country': self.partner_id.country_id.code_iso or '',
                'company': self.partner_id.parent_id.name if self.partner_id.parent_id else '',
                'title': self.partner_id.title.shortcut if self.partner_id.title else '',
                'state': self.partner_id.state_id.name or '',
            },
            'source': {
                'name': self.company_id.name,
                'street': self.company_id.street or '',
                'street2': self.company_id.street2 or '',
                'zip': self.company_id.zip or '',
                'city': "%s - %s" % (self.company_id.city, self.company_id.country_id.name),
                'country': self.company_id.country_id.code_iso or '',
            }
        }

        tracking_number, label_pdf = carrier_acc.get_label(data)
        file_name = 'DE_POST_' + (tracking_number or '') + '.pdf'

        carrier_form = self.env['carrier.form'].search([('prod_code', '=', data['prod_code'])])
        if carrier_form:
            label_pdf = carrier_form.append_carrier_form(label_pdf, picking=self)

        attach = self.env['ir.attachment'].create({
            'name': file_name,
            'datas': label_pdf,
            'datas_fname': file_name,
            'res_id': self.id,
            'res_model': 'stock.picking',
            'type': 'binary'
        })
        picking_vals = {'label_de_attach_id': attach.id}
        
        
        if tracking_number:
            picking_vals.update({'carrier_tracking_ref': tracking_number.replace(' ', '')})
        self.write(picking_vals)    
#             self.env['stock.picking.delivery'].create({
#                 'carrier_id': self.carrier_id.id,
#                 'carrier_tracking_ref': tracking_number.replace(' ', ''),
#                 'date': time.strftime('%Y-%m-%d'),
#                 'picking_id': self.id
#             })
        
        return {
                'type': 'ir.actions.act_url',
                'url': "/web/content/?model=ir.attachment&id=" + str(self.label_de_attach_id.id) + "&field=datas&filename_field=name&download=true",
                'target': 'download',
            }
