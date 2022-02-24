# -*- coding: utf-8 -*-
{
    'name': 'Ecommerce First last name',
    'category': 'other',
    'version': '15.0.1.0.0',
    'author': '',
    'description': """Ecommerce First last name""",
    'sequence': '1',
    'depends': ['website_sale'],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ecommerce_first_last_name/static/src/js/website_sale.js',
        ],
    }
}
