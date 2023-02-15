# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import Warning
from customs.queue_job.job import job

_LOGGER = logging.getLogger(__name__)


# class SaleOrderWizardLine(models.TransientModel):
#     _name = 'sale.order.wizard.line'
#     _description = 'Abandoned Order Line Popup'
#
#     name = fields.Char('Order Reference')
#     date_order = fields.Datetime('Date')
#     partner_id = fields.Many2one('res.partner', 'Customer')
#     user_id = fields.Many2one('res.users', 'Salesperson')
#     amount_total = fields.Float('Total')
#     state = fields.Selection([
#         ('draft', 'Draft Quotation'),
#         ('sent', 'Quotation Sent'),
#         ('cancel', 'Cancelled'),
#         ('waiting_date', 'Waiting Schedule'),
#         ('progress', 'Sales Order'),
#         ('manual', 'Sale to Invoice'),
#         ('shipping_except', 'Shipping Exception'),
#         ('invoice_except', 'Invoice Exception'),
#         ('done', 'Done'),
#     ], 'Status')
#     order_id = fields.Many2one('sale.order', 'Order')
#     wizard_id = fields.Many2one('sale.order.wizard', 'Wizard')


class SaleOrderWizard(models.TransientModel):
    _name = 'sale.order.wizard'
    _description = 'Abandoned Order Popup'

    sale_order_ids = fields.Many2many(
        'sale.order', string='Sale Order')
    max_delete_limit = fields.Integer("Max Record delete limit")

    @api.model
    def default_get(self, fields):
        order_retention_period = safe_eval(self.env['ir.config_parameter'].get_param(
            'abandoned_carts.order_retention_period', '48'))
        date = datetime.now() - timedelta(hours=order_retention_period)

        res = super(SaleOrderWizard, self).default_get(fields)

        # sales_team = self.env['crm.team'].
        # search([('name','in',['Website Sales','Website'])], limit=1)

        system_user = self.sudo().env.ref('base.user_root', False)
        domain = [('state', '=', 'draft'),
                  ('create_date', '<', date.strftime(DF)),
                  ]
        if system_user:
            domain.append(('create_uid', '=', system_user.id))

        sales_team = self.env.ref('sales_team.salesteam_website_sales', False)
        if sales_team:
            domain.append(('team_id', '=', sales_team.id))

        max_delete_batch_limit = safe_eval(self.env['ir.config_parameter'].get_param(
            'abandoned_carts.max_delete_batch_limit', '2000'))
        current_quotation = self.env['sale.order'].search(
            domain, limit=max_delete_batch_limit)
        # lines = []
        # wizard_line_obj = self.env['sale.order.wizard.line']
        # for order in current_quotation:
        #     line = wizard_line_obj.create({'partner_id': order.partner_id.id,
        #                          'date_order': order.date_order,
        #                          'user_id': order.user_id.id,
        #                          'name': order.name,
        #                          'amount_total': order.amount_total,
        #                          'state': order.state,
        #                          'order_id': order.id,
        #                          })
        #     lines.append(line.id)

        res.update({'sale_order_ids': current_quotation.ids,
                    'max_delete_limit': max_delete_batch_limit})
        return res

    @api.model
    def _cron_remove_abandoned_cart_order(self):
        """This function removes sale order and customers"""
        # Remove sale order
        vals = self.default_get(['max_delete_limit', 'sale_order_ids'])
        record = self.create(vals)
        record.action_remove_sale_order()

        # Remove Customers
        vals = self.env['customer.wizard'].default_get(
            ['max_delete_limit', 'customer_ids'])
        record = self.env['customer.wizard'].create(vals)
        record.action_remove_customer()
        return True

    @api.multi
    def action_remove_sale_order(self):
        max_delete_batch_limit = safe_eval(self.env['ir.config_parameter'].get_param(
            'abandoned_carts.max_delete_batch_limit', '2000'))

        ctx = self._context or {}
        selected_ids = ctx.get('deleting_ids', [])
        if selected_ids and ctx.get('manual_remove'):
            order_ids = selected_ids  # self.env['res.partner'].browse(selected_ids)
        else:
            order_ids = self.sale_order_ids.ids

        if len(order_ids) > max_delete_batch_limit:
            raise Warning(
                'For safety reasons, you cannot delete more than %d sale orders \
                together. You can re-open the wizard several times if needed.' \
                % (max_delete_batch_limit))

        # orders = self.sale_order_ids.mapped('order_id')
        user_id = self.env.user.id
        user = self.env.user
        for order_id in order_ids:
            self.with_delay().create_order_remove_queue(order_id, user_id, user)

    def create_order_remove_queue(self, order_id, user_id, user):
        order_obj = self.env['sale.order']
        current_date = datetime.now()
        log_obj = self.env['removed.record.log']

        order = self.env['sale.order'].browse(order_id)
        record_name = order.name
        record_id = order.id
        error = ''

        try:
            order.unlink()
        except Exception as e:
            line = order_obj.browse(order_id)
            line.write({'active': False})
            error = str(e)

        log_obj.create({
            'name': record_name,
            'date': current_date,
            'res_model': 'sale.order',
            'res_id': record_id,
            'user_id': user_id,
            'error': error
        })
        _LOGGER.info('name %s, date %s, model %s, res_id %s, user %s' % (
                    order.name, current_date, 'sale.order', order.id, user.name))

    @api.multi
    def action_remove_sale_order_manual(self):
        ctx = self._context or {}
        deleting_ids = ctx.get('deleting_ids', [])
        if deleting_ids:
            self.with_context(manual_remove=True).action_remove_sale_order()
        return True
