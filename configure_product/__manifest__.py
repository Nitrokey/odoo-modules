# -*- coding: utf-8 -*-
{
    'name': "Configure Product button in Delivery order & Production order",
    'category': 'Hidden',
    'description': """System will add Configure Product button after Add a product button in Delivery order and Production order form. 
    """,
    'version': '12.0.1.0',
    'depends': [
        'stock','mrp'
    ],
    'data': [
             'views/stock_picking_view.xml',
             'views/production_order_view.xml',
             ],
    'author': "Nitrokey GmbH",
    'website': "",
}
