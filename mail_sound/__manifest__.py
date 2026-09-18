{
    "name": "Mail Sound Notifications",
    "version": "18.0.1.1.0",
    "category": "Discuss",
    "summary": "Play sound when receiving messages and meeting reminders",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "license": "AGPL-3",
    "depends": ["mail", "calendar"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "mail_sound/static/src/services/out_of_focus_service_patch.js",
            "mail_sound/static/src/services/calendar_notification_service_patch.js",
        ],
        "web.assets_unit_tests": [
            "mail_sound/static/tests/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
