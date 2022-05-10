{
    'name': 'Calculate product cost',
    'summary': "Calculate product cost from purchase order and Manufacuring order.",
    'version': '15.0.1.0',
    'author': "Nitrokey GmbH",
    'category': 'Product',
    'depends': [
        'product','stock','mrp_account','purchase'
    ],
    'data': [
        'views/product_view.xml',
    ],
    'installable': True,
    'post_init_hook': '_set_is_automatically',
}
