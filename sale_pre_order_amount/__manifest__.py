# -*- coding: utf-8 -*-
{
    'name': 'Sale Pre-Order Amount',
    'version': '12.0.1.0.0',
    'category': 'Inventory',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Sale Pre-Order Amount',
    'description': """
Sale Pre-Order Amount
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

