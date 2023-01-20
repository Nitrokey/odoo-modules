# -*- coding: utf-8 -*-

from odoo import models, api

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.multi
    def _notify_recipients(self, rdata, record, msg_vals,
                           force_send=False, send_after_commit=True,
                           model_description=False, mail_auto_delete=True):
        if msg_vals.get("message_type") == "email":
            channels = rdata.get('channels')
            partner_obj = self.env['res.partner'].sudo()
            IncomingMails = self.env['fetchmail.server'].sudo().search([])
            partners = [(partner) for partner in rdata.get('partners') if partner_obj.browse(partner.get('id')) and partner_obj.browse(partner.get('id')).email in IncomingMails.mapped('user')]
            rdata={'partners': partners, 'channels': channels}
        return super(MailMessage, self)._notify_recipients(rdata=rdata, record=record, msg_vals=msg_vals,
                           force_send=force_send, send_after_commit=send_after_commit,
                           model_description=model_description, mail_auto_delete=mail_auto_delete)
