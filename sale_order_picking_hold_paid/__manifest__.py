# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Order Picking Hold Paid",
    "version": "18.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Hold pickings until invoice is paid based on payment terms",
    "author": "initOS GmbH, Nitrokey GmbH",
    "website": "https://github.com/nitrokey/odoo-modules",
    "license": "AGPL-3",
    "depends": [
        "sale_stock",
        "account",
        "mrp",
        "sale_stock_picking_blocking",
        "web_notify",
    ],
    "data": [
        "views/sale_stock_picking_blocking_reason_view.xml",
        "views/sale_order_views.xml",
    ],
}
