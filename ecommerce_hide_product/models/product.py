from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    hide_accessory_product = fields.Boolean(string="Hide from shop overview")
