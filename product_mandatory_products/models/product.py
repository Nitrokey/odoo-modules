from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mandatory_product_ids = fields.Many2many(
        "product.template",
        "mandatory_optional_rel",
        "src_ids",
        "dest_ids",
    )
