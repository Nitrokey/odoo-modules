{
    'name': 'Mass mailing delivery',
    'version': '12.0',
    'category': '',
    'description': """
        Added delivery_count field in Contact, so we identify how many delivery orders of that contact have.
    """,
    'depends': [
        'sale',
        'stock', 'mass_mailing',
    ],
    'data': [
        'views/res_partner_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'author': "Nitrokey GmbH",
    'license': 'AGPL-3',
    'website': "https://www.nitrokey.com",
}
