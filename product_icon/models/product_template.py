###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    icon_ids = fields.One2many(
        comodel_name="product.template.icon",
        inverse_name="product_template_id",
        string="Icons",
    )
