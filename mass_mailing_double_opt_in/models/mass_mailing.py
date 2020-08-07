# -*- coding: utf-8 -*-
from odoo import fields, models


class MassMailingContactListRel(models.Model):
    _inherit = 'mail.mass_mailing.list_contact_rel'

    access_token = fields.Char('Access Token', copy=False)
