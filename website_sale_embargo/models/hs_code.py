from odoo import fields, models


class HSCode(models.Model):
    _inherit = "hs.code"

    country_id = fields.Many2many(
        "res.country",
        string="Country",
    )
