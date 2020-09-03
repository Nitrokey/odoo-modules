# -*- coding: utf-8 -*-
from odoo import api, fields, models

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    free_shipment = fields.Boolean("Free Shipment")
