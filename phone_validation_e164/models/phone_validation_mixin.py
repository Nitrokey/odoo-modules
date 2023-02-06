# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from .phone_validation import phone_format


class PhoneValidationMixin(models.Model):
    _inherit = "res.partner"

    def _phone_format(self, number, country=None, company=None):
        return phone_format(
            number,
            self.country_id.code if self.country_id else None,
            self.country_id.phone_code if self.country_id else None,
            force_format="E164",
            raise_exception=False,
        )
