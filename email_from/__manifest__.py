{
    "name": "Set Default Email From Address",
    "version": "15.0.1.0.0",
    "category": "Productivity",
    "summary": """
    * User have option to auto set "Email From" value for mail sending from
Odoo for specific selected models.
    * Configuration need to do in Settings --> General Settings menu.
Enter "Email From" and choose the "Models" for that Email From need to change.
    """,
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/email_from.xml",
    ],
    "author": "Nitrokey GmbH",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-tools",
    "auto_install": False,
    "application": False,
    "installable": True,
}
