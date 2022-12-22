import ast
from odoo import fields, models


class EmailFrom(models.Model):
    _name = 'email.from'

    from_email_model_ids = fields.Many2many('ir.model', string='Models')
    email_from = fields.Char(string='Email from')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    email_from_ids = fields.Many2many('email.from')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('email_from_ids.email_from', self.email_from_ids.ids)
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        email = self.env['ir.config_parameter'].sudo().get_param('email_from_ids.email_from')
        if email:
            res.update({'email_from_ids': ast.literal_eval(email)})
        return res


