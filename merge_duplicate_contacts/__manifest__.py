{
    "name": "Merge Duplicate Contacts",
    "category": "Merge Duplicate Contacts",
    "version": "18.0.1.0.0",
    "author": "Nitrokey GmbH",
    "summary": """Merge duplicate partner contact separated by partner fields.""",
    "license": "AGPL-3",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "sequence": "1",
    "depends": ["base", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_domain_email.xml",
        "wizard/merge_contact_view.xml",
    ],
}
