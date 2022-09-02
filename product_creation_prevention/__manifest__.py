# -*- coding: utf-8 -*-
{
    'name': 'Product Creation Prevention',
    'version': '12.0.0.1',
    'description': """Product Creation Prevention""",
    'depends': [
        'account',
        'stock',
        'sale_management',
        'mrp',
        'purchase'
    ],
    'data': [
        'views/account_view.xml',
        'views/sale_view.xml',
        'views/mrp_view.xml',
        'views/picking_view.xml',
        'views/purchase_view.xml',
        ],
    'installable': True,
}
