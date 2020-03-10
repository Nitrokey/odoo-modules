# -*- coding: utf-8 -*-
{
    'name' : 'Multi Picking check Availability',
    'version' : '12.0.1.0.0',
    'summary': '',
    'description': "By installing this module, user can able to check availability of multiple Pickings by single click on one button inside Action button.",
    'category': 'Warehouse',
    'author': 'Nitrokey GmbH, Odoo Community Assosiation (OCA)',
    'website': 'https://github.com/OCA/inventory_check_multiple_availability',
    'license': 'AGPL-3',
    'data': [
        'views/stock_picking_views.xml',
    ],
    'depends': ['stock'],
    'installable': True,
    'application': False,
    'auto_install': False,
    
}
