from odoo import fields, models


class ProductAttributeCustomValue(models.Model):
    _inherit = "product.attribute.custom.value"

    purchase_order_line_id = fields.Many2one(
        "purchase.order.line",
        string="Purchase Order Line",
        required=True,
        ondelete="cascade",
    )
