# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Website Mass Mailing Double opt-in",
    "version": "18.0.1.0.0",
    "category": "Website",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/nitrokey/odoo-modules",
    "license": "AGPL-3",
    "summary": """
    Website Mass Mailing Double opt-in
    Website Mass Mailing Double Opt in is part of website and used to get
    subscription list from newsletter template.

    All the Subscriber can be see under mailing list under newsletter template.
    Added custom template for subscribed message.
    """,
    "depends": [
        "website_mass_mailing",
    ],
    "data": [
        "security/mass_mailing_security.xml",
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "views/mass_mailing_view.xml",
        "views/invalid_confirmation.xml",
        "views/subscribe_template.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "website_mass_mailing_double_opt_in/static/tests/**/*",
            "website_mass_mailing_double_opt_in/static/tests/tours/**/*",
        ],
    },
    "installable": True,
}
