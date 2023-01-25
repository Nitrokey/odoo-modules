{
    "name": "Product Creation Prevention",
    "version": "15.0.1.0.0",
    "summary": """Using this module we can prevent to create new products by
    users except admin user""",
    "depends": ["account", "stock", "sale_management", "mrp", "purchase"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "website": "https://github.com/OCA/server-tools",
    "license": "LGPL-3",
    "installable": True,
}
