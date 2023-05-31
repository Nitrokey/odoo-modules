from odoo import fields, models


class HSCode(models.Model):
    _inherit = "hs.code"

    embargo = fields.Boolean(
        default=False,
        help="Set the embargo on Product in Country",
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
    )
