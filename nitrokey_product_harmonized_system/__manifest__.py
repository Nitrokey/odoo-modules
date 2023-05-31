# -*- coding: utf-8 -*-
# © initOS GmbH 2016
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Nitrokey Product Harmonized System",
    "version": "15.0.0.1",
    "depends": [
        "product_harmonized_system",
        "sale",
        "website_sale",
    ],
    "author": "initOS GmbH",
    "category": "",
    "summary": """
        Add Embargo to Product's HS Code
    """,
    "license": "AGPL-3",
    "data": [
        "views/hs_code.xml",
    ],
    "installable": True,
    "auto_install": False,
}
