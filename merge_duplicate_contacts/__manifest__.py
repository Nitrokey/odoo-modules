{
    "name": "Merge Duplicate Contacts",
    "version": "18.0.1.0.0",
    "summary": "Merge duplicate partner contacts separated by partner fields.",
    "category": "Contacts",
    "author": "Nitrokey GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "license": "AGPL-3",
    "depends": ["base", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_domain_email.xml",
        "wizard/merge_contact_view.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 1,
}
