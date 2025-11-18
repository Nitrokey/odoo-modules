{
    "name": "Ecommerce First Last Name",
    "category": "other",
    "version": "18.0.1.0.0",
    "author": "Nitrokey GmbH",
    "summary": """Ecommerce First last name""",
    "sequence": "1",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "license": "AGPL-3",
    "depends": ["website_sale"],
    "data": [
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "ecommerce_first_last_name/static/src/js/**/*",
        ],
    },
}
