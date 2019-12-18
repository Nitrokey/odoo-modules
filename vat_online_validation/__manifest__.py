# -*- coding: utf-8 -*-

{
    'name': "VAT online validation",
    'description': 'This module will validate VAT number online for the ecommerce customers. If it fails to validate, Odoo shows an error message to the customer.',
    'category': '',
    'version': '1.0',
    'depends': [
                'base_vat',
                ],
    'data': [
            'views/res_config_settings_views.xml',
    ],
    
    'author': "Nitrokey GmbH",
    'website': "https://www.nitrokey.com",


}
