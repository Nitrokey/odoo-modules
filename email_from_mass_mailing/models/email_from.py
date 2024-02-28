from odoo import fields, models


class EmailFrom(models.Model):
    _inherit = "email.from"

    apply_to_mailing = fields.Boolean()
