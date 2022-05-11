# -*- coding: utf-8 -*-
{
    'name': 'Stock Picking Unbuild',
    'version': '15.0.1.0.0',
    'category': 'Website',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Stock Picking Unbuild',
    'description': """
This module allows to create the Unbuild Order from the return picking.
     """,
    'depends': [
        'stock',
        'sale_mrp_link',
    ],
    'data': [
        'views/stock_picking_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
}
