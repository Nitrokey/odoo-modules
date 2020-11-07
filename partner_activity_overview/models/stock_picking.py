# -*- coding: utf-8 -*-
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, body='', subject=None,
                    message_type='notification', subtype=None,
                    parent_id=False, attachments=None,
                    notif_layout=False, add_sign=True, model_description=False,
                    mail_auto_delete=True, **kwargs):
        msg = super(StockPicking, self).message_post(body=body, subject=subject, message_type=message_type,
                    subtype=subtype, parent_id=parent_id, attachments=attachments,
                    notif_layout=notif_layout, add_sign=add_sign, model_description=model_description,
                    mail_auto_delete=mail_auto_delete, **kwargs)
        if not self.partner_id:
            return msg
        part_msg_body = msg.body
        partner_msg = msg.copy(default={'res_id': self.partner_id.id, 'model': 'res.partner', 'body': part_msg_body})
        flag = False
        for line in msg.tracking_value_ids:
            default_vals = {'mail_message_id': partner_msg.id}
            line.copy(default=default_vals)
        return msg

    def _message_log(self, body='', subject=False, message_type='notification', **kwargs):
        msg = super(StockPicking, self)._message_log(body='', subject=False, message_type='notification', **kwargs)
        if not self.partner_id:
            return msg
        part_msg_body = msg.body
        partner_msg = msg.copy(default={'res_id': self.partner_id.id, 'model': 'res.partner', 'body': part_msg_body})
        flag = False
        for line in msg.tracking_value_ids:
            default_vals = {'mail_message_id': partner_msg.id}
            line.copy(default=default_vals)
        return msg
