# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from datetime import timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class SaleOrderWizardLine(models.TransientModel):
    _name = 'sale.order.wizard.line'
    
    name = fields.Char('Order Reference')
    date_order = fields.Datetime('Date')
    partner_id = fields.Many2one('res.partner','Customer')
    user_id = fields.Many2one('res.users','Salesperson')
    amount_total = fields.Float('Total')
    state = fields.Selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status')
    order_id = fields.Many2one('sale.order','Order')
    wizard_id = fields.Many2one('sale.order.wizard','Wizard')
    
class SaleOrderWizard(models.TransientModel):
    _name = 'sale.order.wizard'
    
    sale_order_ids = fields.One2many('sale.order.wizard.line','wizard_id', string='Sale Order')
    max_delete_limit = fields.Integer("Max Record delete limit")
    
    @api.model
    def _cron_remove_abandoned_cart_order(self):
        #Remove sale order
        vals = self.default_get(['max_delete_limit','sale_order_ids'])
        record = self.create(vals)
        record.action_remove_sale_order()
        
        #Remove Customers
        vals = self.env['customer.wizard'].default_get(['max_delete_limit','customer_ids'])
        record = self.env['customer.wizard'].create(vals)
        record.action_remove_customer()
        return True
    
    @api.model
    def default_get(self,fields):
        res_config = self.env['sale.config.settings'].get_default_order_retention_period(fields)
        date = datetime.now() - timedelta(hours=res_config.get('order_retention_period'))
        
        res = super(SaleOrderWizard,self).default_get(fields)
        #sales_team = self.env['crm.case.section'].search([('name','=','Website Sales')], limit=1)
        domain = [('state','=','draft'),('create_date','<',date.strftime(DF))]    
        sales_team = self.env.ref('website.salesteam_website_sales',False)
        
        if sales_team:
            domain.append(('section_id','=',sales_team.id))
        
        
        max_delete_batch_limit = safe_eval(self.env['ir.config_parameter'].get_param('abandoned_carts.max_delete_batch_limit', '2000'))    
        current_quotation = self.env['sale.order'].search(domain, limit=max_delete_batch_limit)
        lines = []
        for order in current_quotation:
            lines.append((0,0,{'partner_id': order.partner_id.id, 
                               'date_order': order.date_order, 
                               'user_id': order.user_id.id, 
                               'name': order.name,
                               'amount_total': order.amount_total,
                               'state': order.state,
                               'order_id': order.id,
                               }))
        res.update({'sale_order_ids':lines, 'max_delete_limit': max_delete_batch_limit})
        return res

    @api.multi
    def action_remove_sale_order(self):
        max_delete_batch_limit = safe_eval(self.env['ir.config_parameter'].get_param('abandoned_carts.max_delete_batch_limit', '2000'))
        if len(self.sale_order_ids)>max_delete_batch_limit:
            raise Warning('For safety reasons, you cannot delete more than %d sale orders together. You can re-open the wizard several times if needed.'%(max_delete_batch_limit))
        current_date = datetime.now()
        log_obj = self.env['removed.record.log']
        orders = self.sale_order_ids.mapped('order_id')
        user = self.env.user
        user_id = self.env.user.id
        for line in orders:
            log_obj.create({
                    'name' : line.name,
                    'date' : current_date,
                    'res_model': 'sale.order',
                    'res_id': line.id,
                    'user_id' : user_id,
                    })
            _logger.info('name %s, date %s, model %s, res_id %s, user %s',(line.name,current_date,'sale.order',line.id,user.name))
            line.unlink()
        return True

    