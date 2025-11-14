import logging

from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSaleFirstLastname(WebsiteSale):
    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        is_main_address,
        **kwargs,
    ):
        """Raise validation save time"""
        invalid_fields, missing_fields, error_messages = (
            super()._validate_address_values(
                address_values, partner_sudo, address_type, use_delivery_as_billing,
                required_fields, is_main_address, **kwargs)
        )
        # Change first or last name
        if partner_sudo and not partner_sudo._can_edit_name():
            full_name = partner_sudo.name or ""
            old_first, old_last = (full_name.split(" ", 1) + [""])[:2]

            new_first = address_values.get("name", "").split(" ", 1)[0]
            new_last = address_values.get("last_name", "")

            first_name_changed = new_first != old_first
            last_name_changed = new_last != old_last

            # Case 1: both changed
            if first_name_changed and last_name_changed:
                invalid_fields.update("name")
                invalid_fields.add("last_name")
            # Case 2: only first name changed
            elif first_name_changed and not last_name_changed:
                invalid_fields.discard("last_name")
                invalid_fields.add("name")
            # Case 3: only last name changed
            elif last_name_changed and not first_name_changed:
                invalid_fields.discard("name")
                invalid_fields.add("last_name")

        return invalid_fields, missing_fields, error_messages

    def _parse_form_data(self, form_data):
        """Call the method when save the address"""
        address_values, extra_form_data = super()._parse_form_data(form_data)
        # Added the first and last name in full name
        last_name = extra_form_data.get("last_name")
        if last_name and address_values.get("name"):
            extra_form_data["first_name"] = address_values.get("name")
            address_values["name"] = address_values.get("name") + " " + last_name
        elif last_name:
            address_values["name"] = last_name
        # Set company type
        company_type = "person"
        if company_type:
            address_values["company_type"] = company_type
        if last_name:
            address_values["last_name"] = last_name
        return address_values, extra_form_data
