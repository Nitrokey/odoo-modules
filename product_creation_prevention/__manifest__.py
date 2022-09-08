{
    'name': 'Product Creation Prevention',
    'version': '12.0.0.1',
    'description': """Product Creation Prevention
    By adding access right we are preventing users creating a products 'on the fly'
    """,
    'depends': [
        'account',
        'stock',
        'sale_management',
        'mrp',
        'purchase'
    ],
    'data': [
        'security/ir.model.access.csv',
        ],
    'installable': True,
}
