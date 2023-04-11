import ast
from odoo import api, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, values):
        new_mail = super(MailMail, self).create(values)
        email_from_ids = self.env['ir.config_parameter'].sudo().get_param('email_from_ids.email_from')
        if email_from_ids:
            email_from_ids = ast.literal_eval(email_from_ids)
            for email_from in self.env['email.from'].search([('id', 'in', email_from_ids)]):
                from_email_model_ids = email_from.from_email_model_ids.mapped('model')
                if from_email_model_ids:
                    if new_mail.model in from_email_model_ids:
                        new_mail.update({'email_from': email_from.email_from})
                        break
        return new_mail
