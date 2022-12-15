# -*- coding: utf-8 -*-
{
    'name': 'Product Lot/Serial Validation',
    'version': '12.0.1.0.0',
    'category': 'Website',
    'author': "Nitrokey GmbH, Odoo Community Association (OCA)",
    'website': 'http://www.erpharbor.com',
    'summary': """This module adds a warning popup message while you are validating picking or 
    manufacturing like "Please verify the Lot/Serial before validating, Product Name: 001
    (i.e. All products names with the Lot/Serial number that is going to be used)".
	The popup warning has two buttons either validate with the Lot/Serial or cancel for change 
	the Lot/Serial and you could change it manually""",
    'description': """This module adds a warning popup message while you are validating picking or 
    manufacturing like "Please verify the Lot/Serial before validating, Product Name: 001
    (i.e. All products names with the Lot/Serial number that is going to be used)".
	The popup warning has two buttons either validate with the Lot/Serial or cancel for change 
	the Lot/Serial and you could change it manually
     """,
    'depends': [
        'stock',
        'mrp',
    ],
    'data': [
        'wizard/stock_tracking_validation_view.xml',
        'wizard/mrp_product_produce_views.xml',
        'views/stock_picking_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
}
