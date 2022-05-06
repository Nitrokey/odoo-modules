from odoo import api, fields, models
from datetime import datetime
import datetime


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    provisioning_time_in_workdays = fields.Datetime(string='Provisioning time in workdays')

