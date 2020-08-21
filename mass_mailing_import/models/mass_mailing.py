# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MassMailingContact(models.Model):
    _inherit = 'mail.mass_mailing.contact'

    temp_create_date = fields.Datetime('Temp Create Date')

    @api.model
    def create(self, vals):
        res = super(MassMailingContact, self).create(vals)
        if vals.get('temp_create_date'):
            self._cr.execute(
                "UPDATE mail_mass_mailing_contact SET create_date='%s' WHERE id=%s" % (res.temp_create_date, res.id)
            )
        return res
