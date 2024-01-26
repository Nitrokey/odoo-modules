from odoo import _, fields, models


class EmailFrom(models.Model):
    _name = "email.from"
    _description = "Email From"
    _order = "sequence"

    def _get_actions(self):
        return [("set", _("Set")), ("keep", _("Keep"))]

    company_id = fields.Many2one("email.from", default=lambda self: self.env.company)
    sequence = fields.Integer(default=10)
    model_ids = fields.Many2many("ir.model", string="Models")
    email_from = fields.Char()
    action = fields.Selection("_get_actions", default="set", required=True)
    active = fields.Boolean(default=True)
