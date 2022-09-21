from odoo import api, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, values):
        new_mail = super(MailMail, self).create(values)
        email_from = self.env['ir.config_parameter'].get_param('email_from.email_from')
        if email_from:
            from_email_model_ids = self.env['ir.config_parameter'].get_param('email_from.from_email_model_ids')
            try:
                from_email_model_ids = eval(from_email_model_ids)
            except Exception as e:
                from_email_model_ids = []
                pass
            if from_email_model_ids:
                default_models = new_mail.env['ir.model'].sudo().browse(from_email_model_ids).mapped('model')
                for mail in new_mail:
                    if mail.model in default_models:
                        mail.update({
                            'email_from': email_from,
                        })
        return new_mail
