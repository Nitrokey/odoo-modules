{
    'name': 'Product Mandatory Products',
    'version': '12.0.1.0.1',
    'category': 'Product',
    'summary': 'Mandatory product selection while checkout',
    'license': 'AGPL-3',
    'depends': [
        'product','website_sale',
    ],
    'data': [
        'views/product_template_view.xml',
        'views/sale_product_configurator_templates.xml',
        'views/templates.xml',
            ],
    # Author
    'author': "Nitrokey GmbH",
    'website': "http://www.nitrokey.com",
    'maintainer': 'Nitrokey GmbH',
    
    'installable': True,
    'auto_install': False,
    'application': False,
}
