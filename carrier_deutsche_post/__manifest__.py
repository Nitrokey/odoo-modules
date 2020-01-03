# -*- coding: utf-8 -*-
#    Copyright 2017 Zedes Technologies

{
    'name': "Delivery Carrier Deutsche Post",
    'description': """
        Deutsche Post Integration. Labels can be retrieved online from the Deutsche Post API and are available as PDF. This module requires a Portokasse account. See https://pypi.org/project/inema/ for details.
    """,
    'category': '',
    'version': '1.0',
    'depends': [
        'stock',
        'delivery',
        'base_delivery_carrier_label',
        #'nitrokey_stock_picking_multiple_carrier',
        #'nitrokey_delivery_setup',
    ],
    'data': [
        'views/delivery.xml',
        'views/carrier_account.xml',
        'views/stock.xml',
        'views/country.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/data_countries.xml',
        'views/carrier_deutsche_post.xml',
    ],
    'qweb': [
        "static/src/xml/picking.xml",
    ],
    'author': "Zedes Technologies",
    'license': 'AGPL-3',
    'website': "http://www.zedestech.com",
}
