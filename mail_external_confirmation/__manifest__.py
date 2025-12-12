{
    "name": "Mail External Confirmation",
    "version": "18.0.1.0.0",
    "summary": """
    This module will show confirmation dialog while sending message
    from chatter when any one follower of the record is not internal user.
    """,
    "author": "Nitrokey GmbH, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/server-tools",
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
