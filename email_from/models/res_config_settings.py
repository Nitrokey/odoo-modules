from odoo import fields, models


class EmailFrom(models.Model):
    _name = "email.from"
    _description = "Email From"

    from_email_model_ids = fields.Many2many("ir.model", string="Models")
    email_from = fields.Char()


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    email_from_ids = fields.Many2many(
        "email.from", related="company_id.email_from_ids", readonly=False
    )


class ResCompany(models.Model):
    _inherit = "res.company"

    email_from_ids = fields.Many2many("email.from")
