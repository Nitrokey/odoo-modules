{
    "name": "Product Creation Prevention",
    "version": "18.0.1.0.0",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "summary": """Using this module we can prevent to create new products by
    users except admin user""",
    "depends": ["account", "stock", "sale_management", "mrp", "purchase"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "license": "LGPL-3",
    "installable": True,
}
