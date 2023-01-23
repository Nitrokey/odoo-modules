{
    "name": "Product Lot/Serial Validation",
    "version": "15.0.1.0.0",
    "category": "Stock",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-tools",
    "summary": """This module adds a warning popup message while you are validating picking or
    manufacturing like "Please verify the Lot/Serial before validating, Product Name: 001
    (i.e. All products names with the Lot/Serial number that is going to be used)".
    The popup warning has two buttons either validate with the Lot/Serial or cancel for change
    the Lot/Serial and you could change it manually""",
    "depends": [
        "stock",
        "mrp",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/stock_tracking_validation_view.xml",
        "views/mrp_production_view.xml",
        "views/stock_picking_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
}
