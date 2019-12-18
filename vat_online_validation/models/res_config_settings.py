# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    must_validate_vat = fields.Boolean('Must validate Vat online?', 
                                       related='company_id.must_validate_vat', 
                                       readonly=False,
                                       help='If checked, system must validate vat number online and show error message if given vat number is not valid in partner/customer.')