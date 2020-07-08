{
    "name": "Stock Warehouse ACL",
    "description": """
    This module adds security group to Inventory app to limit the users
    to see the Stock Operations of the Warehouse assigned to him/her.
    """,
    "category": "Warehouse",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules/",
    "version": "12.0.1.0.0",
    "depends": [
        "stock",
    ],
    "data": [
        "security/security.xml",
        "views/stock_warehouse_view.xml",
    ],
}
