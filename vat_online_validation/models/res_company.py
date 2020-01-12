# -*- coding: utf-8 -*-

from odoo import models,fields

class res_company(models.Model):
    _inherit = 'res.company'
    
    must_validate_vat = fields.Boolean('Mandatory online verification?', help='If checked, system must validate vat number online and show error message if given vat number is not valid in partner/customer.')
