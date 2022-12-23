{
    'name': 'Product Creation Prevention',
    'version': '12.0.1.0.0',
    'description': """Product Creation Prevention
    By adding access right we are preventing users to create products 'on the fly'
    """,
    'depends': [
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        ],
    'installable': True,
}
