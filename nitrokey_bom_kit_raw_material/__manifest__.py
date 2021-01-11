# -*- coding: utf-8 -*-
{
    'name': 'Nitrokey Bom Kit Raw Material',
    'version': '12.0.1.0.0',
    'category': 'Website',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Nitrokey Bom Kit Raw Material',
    'description': """
This module allows to return the raw materials instead of the finish good based on the selected option by the user while return the product.
     """,
    'depends': [
        'stock',
        'sale_mrp_link',
    ],
    'data': [
        'views/stock_picking_view.xml',
        'wizard/stock_picking_return_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
}
