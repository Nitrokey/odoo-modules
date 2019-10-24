# -*- coding: utf-8 -*-

from openerp import models,fields

class res_company(models.Model):
    _inherit = 'res.company'
    
    must_validate_vat = fields.Boolean('Must validate Vat online?', help='If checked, system must validate vat number online and show error message if given vat number is not valid in partner/customer.')