{
    "name": "Mass mailing delivery",
    "version": "15.0.1.0.0",
    "category": "",
    "summary": """
Added delivery_count field in Contact,
so we identify how many delivery orders of that contact have.
    """,
    "depends": ["mass_mailing", "sale_stock"],
    "data": [
        "views/res_partner_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "author": "Nitrokey GmbH",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-tools",
}
