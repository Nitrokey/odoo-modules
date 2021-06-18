{
    'name': 'Bitcoin Payment Customization',
    'licence': 'AGPL-3',
    'category': 'Customization',
    'summary': 'Bitcoin Payment Customization',
    'version': '12.0.1.2.0',
    'license': 'AGPL-3',
    'author': 'Nitrokey GmbH, Odoo Community Association (OCA)',
    'depends': ['payment_bitcoin'],
    'data': [
        'data/data.xml',
        'views/res_config_settings_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
