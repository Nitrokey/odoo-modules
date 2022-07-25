{
    'name': 'Product Mandatory Products',
    'version': '15.0.1.0.1',
    'category': 'Product',
    'summary': 'Mandatory product selection while checkout',
    'license': 'AGPL-3',
    'depends': [
        'product', 'website_sale', 'website_sale_product_configurator',
    ],
    'data': [
        'views/product_template_view.xml',
        'views/template.xml',
    ],

    # Author
    'author': "Nitrokey GmbH",
    'website': "http://www.nitrokey.com",
    'maintainer': 'Nitrokey GmbH',
    'assets': {
        'web.assets_frontend': [
            'product_mandatory_products/static/src/js/website_sale_options.js',
        ],

    },
    'installable': True,
    'auto_install': False,
    'application': False,

}
