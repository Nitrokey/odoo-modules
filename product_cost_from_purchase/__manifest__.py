{
    'name': 'Calculate product cost',
    'summary': "Calculate product cost from purchase order and Manufacuring order.",
    'version': '12.0.1.0.0',
    'author': "Nitrokey GmbH",
    'category': 'Product',
    'depends': [
        'product','stock','mrp_bom_cost',
    ],
    'data': [
        'views/product_view.xml',
    ],
    'installable': True,
}
