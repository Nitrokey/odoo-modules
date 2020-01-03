{
    'name': "Newsletter subscription via Sendy",
    'description': '',
    'category': '',
    'version': '12.0.1.0.0',
    'depends': ['mail'],
    'data': [
        'data/ir_config.xml',
        'views/res_partner.xml',
    ],
    'author': "initOS",
    'website': "http://www.initos.com",
    'external_dependencies': {
        'python': ['pysendy'],
    }
}
