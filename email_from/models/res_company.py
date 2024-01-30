from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    email_from_ids = fields.One2many("email.from", "company_id")
