import ast
from odoo import fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    from_email_model_ids = fields.Many2many('ir.model', 'res_config_ir_model_mail_from_rel', 'config_id', 'model_id', string='Models')
    email_from = fields.Char(string='Email from', config_parameter='email_from.email_from')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('email_from.from_email_model_ids', self.from_email_model_ids.ids)
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        from_email_model_ids = self.env['ir.config_parameter'].sudo().get_param('email_from.from_email_model_ids')
        if from_email_model_ids:
            res.update({'from_email_model_ids': ast.literal_eval(from_email_model_ids)})
        return res
