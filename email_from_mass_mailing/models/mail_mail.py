import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _unique_key_for_mail(self):
        return (
            bool(self.mailing_id),
            self.mailing_id.mailing_model_id.model or super()._unique_key_for_mail(),
        )
