{
    "name": "Website Product Attribute Description",
    "version": "18.0.1.0.0",
    "category": "Website",
    "author": "ERP Harbor Consulting Services, Nitrokey GmbH",
    "website": "https://github.com/nitrokey/odoo-modules",
    "summary": """
    This module adds the information icon next to the attribute name in the
    website and display the related description on mouse hover.
     """,
    "depends": ["product_attribute_description", "website_sale"],
    "data": [
        "views/template.xml",
    ],
    "assets": {
        "website.frontend_assets": [
            "/website_product_attribute_description/static/src/css/tooltip.css",
            "/website_product_attribute_description/static/src/js/tooltip.js",
        ],
    },
    "license": "AGPL-3",
    "installable": True,
}
