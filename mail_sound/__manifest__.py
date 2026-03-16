{
    "name": "Mail Sound Notifications",
    "version": "18.0.1.0.0",
    "category": "Discuss",
    "summary": "Play sound when receiving messages",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "license": "AGPL-3",
    "depends": ["mail"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "mail_sound/static/src/services/out_of_focus_service_patch.js",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
