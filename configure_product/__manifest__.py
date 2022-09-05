{
    "name": "Configure Product",
    "category": "Hidden",
    "summary": """The system will display Configure Product wizard after
    Adding a product to the sale order and purchase order form.
    """,
    "version": "15.0.1.0.0",
    "depends": [
        "sale_product_configurator",
        "purchase",
        "sale_management",
    ],
    "data": [
        "views/purchase_view.xml",
    ],
    "author": "Nitrokey GmbH",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/server-tools",
}
