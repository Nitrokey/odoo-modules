# -*- coding: utf-8 -*-
{
    'name': 'Partner Delivery Link',
    'version': '15.0.1.0.0',
    'category': 'Website',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': """ 
    Partner Delivery Link
    This module adds a smart button in Partner to open the Delivery Orders of the related partner.
    """,
    'depends': ['stock'],
    'data': [
        'views/res_partner_view.xml',
    ],
    'installable': True,
}
