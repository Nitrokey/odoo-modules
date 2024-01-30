{
    "name": "Set Default Email From Address",
    "version": "15.0.1.0.0",
    "category": "Productivity",
    "summary": """
        This module allows to configure "Email From" value for mail sending from
        Odoo for specific selected models. The configuration need to do in Settings
        --> General Settings menu. Click "Email From" and choose the "Models" for that
        Email From need to change and action Set. Leave the model empty to define an
        email address used by default for all models. Choose action Keep if you don't
        want to overwrite the email address used.""",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/email_from.xml",
        "views/res_config_settings_views.xml",
    ],
    "author": "Nitrokey GmbH",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-tools",
    "auto_install": False,
    "application": False,
    "installable": True,
}
