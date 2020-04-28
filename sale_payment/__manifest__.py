# -*- coding: utf-8 -*-
{
    'name': 'Nitrokey Sale Payment',
    'version': '12.0.1.0.0',
    'category': 'Website',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Nitrokey Sale Payment',
    'description': """
    This module adds the new fields which are available in v8 but not in v12.
    and makes the other nitrokey custom module compatible with the v12.
     """,
    'depends': [
        'website_sale',
        'stock_picking_on_hold'
    ],
    'data': [
    ],
    'installable': True,
}
