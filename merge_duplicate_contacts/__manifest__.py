{
    "name": "Merge Duplicate Contacts",
    "version": "18.0.1.0.0",
    "summary": "Merge duplicate partner contacts separated by partner fields.",
    "category": "Contacts",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "license": "AGPL-3",
    "depends": ["base", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_domain_email.xml",
        "wizard/merge_contact_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "merge_duplicate_contacts/static/src/css/merge_radio.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 1,
}
