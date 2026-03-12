{
    "name": "Mail Confirm External Recipient",
    "version": "18.0.1.0.0",
    "category": "Discuss",
    "summary": "Confirm sending message if there are external recipients",
    "author": "Nitrokey",
    "website": "https://github.com/Nitrokey/odoo-modules/",
    "depends": ["mail"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "mail_confirm_external_recipient/static/src/core/common/composer_patch.js",
            "mail_confirm_external_recipient/static/src/chatter/web/mail_composer_send_dropdown_patch.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
