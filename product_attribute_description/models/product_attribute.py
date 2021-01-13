# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    description = fields.Text('Description', translate=True)
