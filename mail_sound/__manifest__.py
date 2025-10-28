# -*- coding: utf-8 -*-
{
    "name": "Mail Sound Notifications",
    "version": "15.0.2.0.0",
    "category": "Discuss",
    "summary": "Play sound when receiving messages regardless of focus",
    "author": "Nitrokey GmbH",
    "website": "https://www.nitrokey.com",
    "license": "AGPL-3",
    "depends": ["mail"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "mail_sound/static/src/models/messaging_notification_handler/messaging_notification_handler.js",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
