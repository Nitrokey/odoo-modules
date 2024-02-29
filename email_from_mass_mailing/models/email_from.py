from odoo import fields, models


class EmailFrom(models.Model):
    _inherit = "email.from"

    apply_to_mailing = fields.Boolean()

    def _unique_key_for_model(self, model):
        return self.apply_to_mailing, model
