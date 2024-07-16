from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipping_label_ids = fields.Many2many("ir.attachment", string="Labels", copy=False)
