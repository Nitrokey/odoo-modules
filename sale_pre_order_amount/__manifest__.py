# -*- coding: utf-8 -*-
{
    'name': 'Sale Pre-Order Amount',
    'version': '12.0.1.0.0',
    'category': 'Inventory',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Sale Pre-Order Amount',
    'description': """
This module adds a smart button in Product to open the confirmed/assigned Stock Moves (Sale Pre-Order Amount) of the related product.
     """,
    'depends': [
        'sale_stock',
    ],
    'data': [
        'views/nitrokey_pre_order_view.xml',
        'views/product_view.xml',
    ],
    'installable': True,
}
