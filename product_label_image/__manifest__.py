{
    "name": "Product Label Image",
    "category": "other",
    "version": "18.0.1.0.1",
    "summary": """Prints product barcode along with product image""",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/Nitrokey/odoo-modules",
    "license": "AGPL-3",
    "depends": ["product"],
    "data": [
        "reports/product_template_report.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "product_label_image/static/src/scss/product_label_image.scss"
        ],
    },
}
