{
    'name': 'Product Creation Prevention',
    'version': '12.0.0.1',
    'description': """Product Creation Prevention""",
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
