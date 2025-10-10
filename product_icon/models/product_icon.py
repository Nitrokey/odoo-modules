###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductIcon(models.Model):
    _name = "product.icon"
    _description = "Product icon"
    _order = "sequence, id"

    name = fields.Char(
        required=True,
    )
    sequence = fields.Integer()
    product_template_id = fields.Many2one(
        comodel_name="product.template",
        string="Product template",
        index=True,
        required=True,
    )
    image_1920 = fields.Image(
        string="Image",
        required=True,
    )
    image_128 = fields.Image(
        string="Image 128",
        related="image_1920",
        max_width=128,
        max_height=128,
        store=True,
    )
    image_256 = fields.Image(
        string="Image 256",
        related="image_1920",
        max_width=256,
        max_height=256,
        store=True,
    )
