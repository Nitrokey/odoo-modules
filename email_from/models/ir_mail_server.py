from odoo import api, models


class MailServer(models.Model):
    _inherit = "ir.mail_server"

    @api.model
    def _get_default_from_address(self):
        # Disable default from function
        return False
