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
    ],
    "data": [
        "view/res_company.xml",
        "view/delivery_carrier.xml",
    ],
    "author": "Vraja Technologies, initOS",
    "website": "http://www.vrajatechnologies.com",
    "maintainer": "initOS",
    "installable": True,
}
