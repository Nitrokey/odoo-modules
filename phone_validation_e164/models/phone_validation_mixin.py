# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from .phone_validation import phone_format

class PhoneValidationMixin(models.AbstractModel):
    _inherit = 'phone.validation.mixin'

    def phone_format(self, number, country=None, company=None):
        country = country or self._phone_get_country()
        if not country:
            return number
        return phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            always_international=False,
            raise_exception=False,
        )
