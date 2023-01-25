{
    "name": "Product Automatic Cost",
    "summary": """Calculate product cost automatically from purchase order
 or Manufacuring order.""",
    "version": "15.0.1.0.0",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/OCA/server-tools",
    "license": "LGPL-3",
    "category": "Product",
    "depends": ["product", "stock", "mrp_account", "purchase"],
    "data": [
        "views/product_view.xml",
    ],
    "installable": True,
    "post_init_hook": "_set_is_automatically",
}
