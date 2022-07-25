from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_template_id = fields.Many2one(
        "product.template",
        string="Product Template",
        related="product_id.product_tmpl_id",
        domain=[("purchase_ok", "=", True)],
    )
    is_configurable_product = fields.Boolean(
        "Is the product configurable?",
        related="product_template_id.has_configurable_attributes",
    )
    product_template_attribute_value_ids = fields.Many2many(
        related="product_id.product_template_attribute_value_ids", readonly=True
    )
    product_no_variant_attribute_value_ids = fields.Many2many(
        "product.template.attribute.value",
        string="Product attribute values that do not create variants",
        ondelete="restrict",
    )
    product_custom_attribute_value_ids = fields.One2many(
        "product.attribute.custom.value",
        "purchase_order_line_id",
        string="Custom Values",
        copy=True,
    )
