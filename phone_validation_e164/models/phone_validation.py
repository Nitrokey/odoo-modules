# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError
from odoo.addons.phone_validation.tools.phone_validation import phone_parse,phone_format
import logging
import phonenumbers
_logger = logging.getLogger(__name__)

def phone_format(number, country_code, country_phone_code, force_format='E164', raise_exception=True):
    try:
        phone_nbr = phone_parse(number, country_code)
    except (phonenumbers.phonenumberutil.NumberParseException, UserError) as e:
        if raise_exception:
            raise
        else:
            _logger.warning(_('Unable to format %s:\n%s'), number, e)
            return number
    return phonenumbers.format_number(phone_nbr, phonenumbers.PhoneNumberFormat.E164)
