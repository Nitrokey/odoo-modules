# -*- coding: utf-8 -*-

{
    'name': 'Bitcoin Payment Acquirer',
    'licence': 'AGPL-3',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Bitcoin Transfer Implementation',
    'version': '12.0.1.2.0',
    'description': """Bitcoin Transfer Payment Acquirer. The actual payment
                   and wallet is kept separate. Bitcoin address need to be
                   imported into this module. Each order gets an own dedicated
                   Bitcoin address. The actual transaction needs to be
                   registered manually.""",
    'author': 'Nitrokey GmbH, Odoo Community Assosiation (OCA)',
    'website': 'https://github.com/OCA/payment_bitcoin',
    'depends': ['payment', 'website_sale', 'sale_payment','base_automation'],
    'data': [
        'views/bitcoin_views.xml',
        'views/payment_bitcoin_templates.xml',
        'views/templates.xml',
        'views/cart.xml',
        'views/res_config_settings_view.xml',
        'data/payment_acquirer_data.xml',
        'data/base_automation.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
