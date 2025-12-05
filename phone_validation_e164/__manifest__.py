# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Phone Validation E164",
    "summary": "Enforces E.164 phone number formatting for res.partner records."
    "Phone and mobile fields are validated and saved in E.164 format,"
    "overriding Odoo core behavior. Supports website/API saves.",
    "category": "Phone",
    "license": "AGPL-3",
    "version": "18.0.1.0.0",
    "external_dependencies": {"python": ["phonenumbers"]},
    "depends": ["phone_validation"],
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
}
