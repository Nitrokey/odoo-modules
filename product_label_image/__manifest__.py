{
    "name": "Product Label Image",
    "category": "",
    "version": "15.0.1.0.1",
    "author": "Nitrokey GmbH",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-tools",
    "summary": """Prints product barcode along with product image""",
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
