# -*- coding: utf-8 -*-

from datetime import datetime
import logging
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval


_LOGGER = logging.getLogger(__name__)


class CustomerWizardLine(models.TransientModel):
    """Abandoned Customer Line Popup"""
    _name = 'customer.wizard.line'
    _description = 'Abandoned Customer Line Popup'

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', 'Customer')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    wizard_id = fields.Many2one('customer.wizard', 'Wizard')

    def action_view_customer(self):
        try:
            form_id = self.env['ir.model.data'].sudo().get_object_reference('base', 'view_partner_form')[1]
        except ValueError:
            form_id = False
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'views': [(form_id, 'form')],
            'view_id': form_id,
            'target': 'new',
        }
        

class CustomerWizard(models.TransientModel):
    """Abandoned Customer Popup"""
    _name = 'customer.wizard'
    _description = 'Abandoned Customer Popup'

    customer_ids = fields.One2many(
        'customer.wizard.line', 'wizard_id', string='Customers')
    max_delete_limit = fields.Integer("Max Record delete limit")
    
    
    
    
    @api.model
    def default_get(self, fields):

        res = super(CustomerWizard, self).default_get(fields)
        max_delete_batch_limit = safe_eval(self.env['ir.config_parameter'].get_param(
            'abandoned_carts.max_delete_batch_limit', '2000'))
        
        system_user = self.sudo().env.ref('base.user_root', False)
        system_user_filter = ''
        if system_user:
            system_user_filter = 'and p.create_uid='+str(system_user.id)
        qry = """SELECT p.id
FROM res_partner p
WHERE
    NOT EXISTS (SELECT 1 FROM crm_lead as lead WHERE lead.partner_id = p.id) and
    NOT EXISTS (SELECT 1 FROM calendar_event_res_partner_rel ce WHERE ce.res_partner_id = p.id) and
    NOT EXISTS (SELECT 1 FROM crm_phonecall call WHERE call.partner_id=p.id) and
    NOT EXISTS (SELECT 1 FROM account_invoice inv WHERE inv.partner_id = p.id) and
    NOT EXISTS (SELECT 1 FROM sale_order o  WHERE o.partner_id = p.id or o.partner_invoice_id=p.id or o.partner_shipping_id=p.id) and
    NOT EXISTS (SELECT 1 FROM account_move move  WHERE move.partner_id = p.id) and
    NOT EXISTS (SELECT 1 FROM account_move_line line  WHERE line.partner_id = p.id) and
    NOT EXISTS (SELECT 1 FROM project_task task  WHERE task.partner_id = p.id) and 
    p.active is not true and
    p.customer and
    p.id not in (select partner_id from res_users union all select partner_id from res_company order by partner_id)
    %s
    order by p.id desc
    limit %d
    """ %(system_user_filter,max_delete_batch_limit)
    
        partner_obj = self.env['res.partner']
        #         if hasattr(partner_obj, 'newsletter_sendy'):
        #             qry += " and not p.newsletter_sendy"
        self._cr.execute(qry)
        data = self._cr.fetchall()
        customer_ids = [p[0] for p in data]
        wizard_line_obj = self.env['customer.wizard.line']
        lines = []
        for customer in partner_obj.browse(customer_ids):
            line = wizard_line_obj.create({'partner_id': customer.id, 'email': customer.email, 'phone': customer.phone, 'name': customer.name})
            lines.append(line.id)
#             lines.append((0, 0, {'partner_id': customer.id, 'email': customer.email,
#                                  'phone': customer.phone, 'name': customer.name}))
        res.update(
            {'customer_ids': [(6,0,lines)], 'max_delete_limit': max_delete_batch_limit})
        return res

    @api.multi
    def action_remove_customer(self):

        max_delete_batch_limit = safe_eval(self.env['ir.config_parameter'].get_param(
            'abandoned_carts.max_delete_batch_limit', '2000'))
        ctx = self._context or {}
        selected_ids = ctx.get('deleting_ids',[])
        if selected_ids and ctx.get('manual_remove'):
            customers = self.env['customer.wizard.line'].browse(selected_ids)
        else:
            customers = self.customer_ids
            
        if len(customers) > max_delete_batch_limit:
            raise Warning(
                'For safety reasons, you cannot delete more than %d Customer together. \
                You can re-open the wizard several times if needed.' % max_delete_batch_limit)

        current_date = datetime.now()
        log_obj = self.env['removed.record.log']
        user = self.env.user
        user_id = user.id

        customer_ids = customers.mapped('partner_id').ids
        partner_obj = self.env['res.partner']
        newsletter_sendy = hasattr(
            partner_obj, 'newsletter_sendy') and True or False

        for partner_id in customer_ids:
            # Browse one record only, because if partner linked to some record and \
            # raise exception when deleting record, than system will just rollback that transaction.
            self._cr.execute('SAVEPOINT remove_partner')
            line = partner_obj.browse(partner_id)
            record_name = line.name
            record_id = line.id
            error = ''
            try:
                if newsletter_sendy and line.newsletter_sendy:
                    self._cr.execute(
                        "update res_partner set newsletter_sendy=false where id=%d" % partner_id)
                    line.refresh()
                line.unlink()
            except Exception as e:
                self._cr.execute('ROLLBACK TO SAVEPOINT remove_partner')
                self._cr.execute('SAVEPOINT remove_partner')
                line = partner_obj.browse(partner_id)
                line.write({'active': False})
                error = str(e)
                

            log_obj.create({
                'name': record_name,
                'date': current_date,
                'res_model': 'res.partner',
                'res_id': record_id,
                'user_id': user_id,
                'error' : error
            })
            _LOGGER.info('name %s, date %s, model %s, res_id %s, user %s'%(record_name, current_date, 'res.partner', record_id, user.name))
            self._cr.execute('RELEASE SAVEPOINT remove_partner')
    
    @api.multi
    def action_remove_customer_manual(self):
        ctx = self._context or {}
        deleting_ids = ctx.get('deleting_ids',[])
        if deleting_ids:
            self.with_context(manual_remove=True).action_remove_customer()
        
        return True
    
    