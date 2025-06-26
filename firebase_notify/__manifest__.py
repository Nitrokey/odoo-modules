{
    "name": "Firebase Notifications",
    "version": "15.0.1.0.0",
    "summary": "Send Firebase notifications for chat and inbox messages",
    "author": "Nitrokey GmbH",
    "depends": ["base", "mail", "firebase_integration"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_users_views.xml",
        "views/test_template.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "firebase_notify/static/src/js/firebase_notify.js",
            "firebase_notify/static/src/js/firebase_integration.js",
            "firebase_notify/static/src/xml/firebase_notify_templates.xml",
        ],
    },
    "images": [],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
}
