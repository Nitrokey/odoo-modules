{
    "name": "DHL Parcel (Post & Parcel Germany) Integration",
    "category": "Website",
    "version": "18.0.1.0.0",
    "summary": """
        Create DHL Parce DE shipments from Odoo,
        update tracking information in Odoo from DHL,
        generate shipping label in Odoo.
    """,
    "license": "AGPL-3",
    "depends": [
        "stock_delivery",
        "base_iso3166",
        "stock_picking_declared_value",
    ],
    "data": [
        "data/ir_cron.xml",
        "views/res_company.xml",
        "views/delivery_carrier.xml",
        "views/stock_picking.xml",
    ],
    "author": "Vraja Technologies, initOS, Nitrokey",
    "website": "https://www.nitrokey.com",
    "maintainer": ["initOS", "Nitrokey"],
    "installable": True,
}
