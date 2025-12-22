{
    "name": "Mail External Confirmation",
    "version": "18.0.1.0.0",
    "summary": """
    This module will show confirmation dialog while sending message
    from chatter when any one follower of the record is not internal user.
    - Pupup the message when anyone mension in chatter or notes
    Displays a confirmation dialog when mentioning (@) an external user
    in chatter messages or internal notes.
    - Triggers a confirmation popup when all followers are removed,
    but the message is still being sent to partner email addresses
    that are not internal users.
    """,
    "author": "Nitrokey GmbH",
    "license": "LGPL-3",
    "website": "https://github.com/nitrokey/odoo-modules",
    "maintainer": "Nitrokey GmbH",
    "depends": ["mail", "base"],
    "data": [],
    "installable": True,
    "assets": {
        "web.assets_backend": [
            (
                "after",
                "mail/static/src/core/common/composer.js",
                "mail_external_confirmation/static/src/core/common/composer.js",
            ),
        ],
    },
}
