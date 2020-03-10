{
    'name': "Newsletter subscription via Sendy",
    'description': 'Customer will be subscriped to a newsletter via sendy',
    'version': '12.0.1.0.0',
    'depends': ['mail'],
    'data': [
        'data/ir_config.xml',
        'views/res_partner_views.xml',
    ],
    'author': "Nitrokey GmbH, Odoo Community Assosiation (OCA)",
    'license': 'AGPL-3',
    'website': "https://github.com/OCA/base_newsletter_sendy",
    'external_dependencies': {
        'python': ['pysendy'],
    }
}
