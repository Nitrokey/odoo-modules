# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Website Mass Mailing Double opt-in Nitrokey",
    "version": "18.0.1.0.0",
    "author": "Nitrokey GmbH",
    "license": "AGPL-3",
    "website": "http://www.nitrokey.com",
    "summary": """
    Mass Mailing Double opt-in module subscribe the newsletter at the time of
    payment processing also checks if user has already subscribed or not,
    Added only nitrokey related custom code into this module from
    "website_mass_mailing_double_opt_in"
    """,
    "depends": [
        "website_sale_mass_mailing",
        "website_mass_mailing_double_opt_in",
        "website_payment",
        "nitrokey_setup",
        "nitrokey_reports",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
    ],
    "installable": True,
}
