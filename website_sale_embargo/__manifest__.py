# © initOS GmbH 2023
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Website Sales Embargo",
    "version": "15.0.1.0.0",
    "depends": [
        "product_harmonized_system",
        "sale",
        "website_sale",
    ],
    "author": "Nitrokey GmbH",
    "category": "",
    "summary": """
        Add Embargo to Product's HS Code
    """,
    "website": "https://github.com/OCA/server-tools",
    "license": "AGPL-3",
    "data": [
        "views/hs_code.xml",
    ],
    "installable": True,
    "auto_install": False,
}
