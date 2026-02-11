{
    "name": "Website Product Configurator Restriction",
    "version": "18.0.1.0.0",
    "summary": """Website configure products restriction in e-shop""",
    "author": "Nitrokey GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/product-configurator",
    "license": "AGPL-3",
    "category": "website",
    "depends": [
        "website_sale",
        "product_configurator",
        "product_configurator_sale",
    ],
    "data": [
        "security/configurator_security.xml",
        "data/data_file.xml",
        "data/website_tour.xml",
    ],
    "images": ["static/description/cover.png"],
    "application": True,
    "installable": True,
    "assets": {
        "web.assets_frontend": [
            "website_product_configurator_restriction/static/src/js/variant_mixin.js",
        ],
        "web.assets_tests": [
            "website_product_configurator_restriction/static/tests/**/*",
            "website_product_configurator_restriction/static/tests/tours/website_config_restrict_tour.js",
        ],
    },
}
