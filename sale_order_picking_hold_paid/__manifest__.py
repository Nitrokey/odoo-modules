# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Order Picking Hold Paid",
    "version": "15.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Hold pickings until invoice is paid based on payment terms",
    "author": "Nitrokey GmbH",
    "website": "https://github.com/OCA/server-tools",
    "license": "AGPL-3",
    "readme": "README.rst",
    "depends": [
        "sale_stock",
        "account",
        "mrp",
        "sale_stock_picking_blocking",
    ],
    "data": [
        "views/account_payment_term_views.xml",
        "views/sale_stock_picking_blocking_reason_view.xml"
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
