# -*- coding: utf-8 -*-
import logging

import phonenumbers

from odoo import api, models
from odoo.exceptions import UserError

from odoo.addons.phone_validation.tools.phone_validation import phone_parse

_logger = logging.getLogger(__name__)


def _format_number_to_e164(number_str, country):
    """
    Your E164 helper function.
    Takes a number string and a res.country record.
    """
    if not number_str:
        return number_str

    country_code = country.code if country else None

    try:
        phone_nbr = phone_parse(number_str, country_code)
        return phonenumbers.format_number(
            phone_nbr, phonenumbers.PhoneNumberFormat.E164
        )
    except (phonenumbers.phonenumberutil.NumberParseException, UserError) as e:
        _logger.warning(f"Could not apply E164 formatting: {number_str} ({e})")
        return number_str


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # --- 1. FIX Odoo Core Behavior ---
    # Override the @onchange methods to use E164 instead of INTERNATIONAL

    def _format_onchange_number(self, field_name):
        number = getattr(self, field_name)
        country = self.country_id if self.country_id else None
        if number:
            formatted = _format_number_to_e164(number, country)
            # If formatting failed and number starts with '+', try without country
            if formatted == number and number.startswith('+'):
                formatted_intl = _format_number_to_e164(number, None)
                if formatted_intl != number:
                    setattr(self, field_name, formatted_intl)
                    return
            setattr(self, field_name, formatted)

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        self._format_onchange_number('phone')

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        self._format_onchange_number('mobile')

    # --- 2. ADD Save Logic (for Website/API) ---
    # Catches all save actions that bypass @onchange

    def _get_country_for_phone_format(self, vals):
        """ Helper to find the country (new or existing) """
        if vals.get('country_id'):
            return self.env['res.country'].browse(vals['country_id'])
        if self:
            return self[0].country_id
        return self.env['res.country'].browse([])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            country = self._get_country_for_phone_format(vals)
            if vals.get('phone'):
                vals['phone'] = _format_number_to_e164(vals['phone'], country)
            if vals.get('mobile'):
                vals['mobile'] = _format_number_to_e164(vals['mobile'], country)
        return super().create(vals_list)

    def write(self, vals):
        if 'phone' in vals or 'mobile' in vals:
            country = self._get_country_for_phone_format(vals)
            if vals.get('phone'):
                vals['phone'] = _format_number_to_e164(vals['phone'], country)
            if vals.get('mobile'):
                vals['mobile'] = _format_number_to_e164(vals['mobile'], country)
        return super().write(vals)
