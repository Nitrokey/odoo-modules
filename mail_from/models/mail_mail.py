from odoo import api, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.multi
    def _send_prepare_values(self, partner=None):
        email_from = self.env['ir.config_parameter'].get_param('mail_from.email_from')
        if email_from:
            from_email_model_ids = self.env['ir.config_parameter'].get_param('mail_from.from_email_model_ids')
            try:
                from_email_model_ids = eval(from_email_model_ids)
            except Exception as e:
                from_email_model_ids = []
                pass
            if from_email_model_ids:
                default_models = self.env['ir.model'].sudo().browse(from_email_model_ids).mapped('model')
                for mail in self:
                    if mail.model in default_models:
                        mail.write({
                            'email_from': email_from,
                        })
        return super(MailMail, self)._send_prepare_values(partner)
