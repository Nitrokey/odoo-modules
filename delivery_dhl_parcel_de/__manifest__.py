{
    "name": "DHL Parcel (Post & Parcel Germany) Integration",
    "category": "Website",
    "version": "18.0.1.0.2",
    "summary": """
        Create DHL Parce DE shipments from Odoo,
        update tracking information in Odoo from DHL,
        generate shipping label in Odoo.
    """,
    "license": "AGPL-3",
    "depends": [
        "stock_delivery",
        "delivery_carrier_account",
        "base_iso3166",
        "stock_picking_declared_value",
        "mrp",
        "product_harmonized_system",
    ],
    "data": [
        "data/data.xml",
        "data/ir_cron.xml",
        "views/carrier_account_views.xml",
        "views/delivery_carrier.xml",
        "views/stock_picking.xml",
    ],
    "author": "Vraja Technologies, initOS, Nitrokey",
    "website": "https://github.com/Nitrokey/odoo-modules/",
    "maintainer": ["initOS", "Nitrokey"],
    "installable": True,
}
