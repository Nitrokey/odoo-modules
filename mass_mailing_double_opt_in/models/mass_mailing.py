# -*- coding: utf-8 -*-
from odoo import fields, models


class MailingContactSubscription(models.Model):
    _inherit = 'mailing.contact.subscription'

    access_token = fields.Char('Access Token', copy=False)
    mail_language = fields.Char('Mail Language')
