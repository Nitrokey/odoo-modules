{
    "name": "Product Creation Prevention",
    "version": "15.0.1.0.0",
    "summary": """Product Creation Prevention
    By adding access right we are preventing users to create products 'on the fly'
    """,
    "depends": ["account", "stock", "sale_management", "mrp", "purchase"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "website": "https://github.com/OCA/server-tools",
    "license": "LGPL-3",
    "installable": True,
}
