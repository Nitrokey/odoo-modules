{
    "name": "Product Mandatory Products",
    "version": "15.0.1.0.1",
    "category": "Product",
    "summary": "Show Mandatory product selection popup while Add to Cart.",
    "license": "AGPL-3",
    "depends": [
        "product",
        "website_sale",
        "website_sale_product_configurator",
    ],
    "data": [
        "views/product_template_view.xml",
        "views/template.xml",
    ],
    # Author
    "author": "Nitrokey GmbH",
    "website": "https://github.com/OCA/server-tools",
    "maintainer": "Nitrokey GmbH",
    "assets": {
        "web.assets_frontend": [
            "product_mandatory_products/static/src/js/website_sale_options.js",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
