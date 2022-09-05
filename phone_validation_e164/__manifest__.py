# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Phone Validation E164",
    "summary": """
    There are formatters for the three types of phone number formats:
     1. The international format
     2. The national format
     3. The E164 format
    By default the E164 format we have added for partner form while checkout in the website.
    """,
    "category": "Phone",
    "license": "AGPL-3",
    "version": "15.0.1.0.0",
    "external_dependencies": {"python": ["phonenumbers"]},
    "depends": ["phone_validation"],
    "author": "Nitrokey GmbH",
    "website": "https://github.com/OCA/server-tools",
}
