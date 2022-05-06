{
    'name': 'Website Sale Stock Provisioning Time',
    'summary': 'Display provisioning time for a product in shop online',
    'version': '12.0.1.0',
    'category': 'Website',

    # Author
    'author': "Nitrokey GmbH",
    'website': "http://www.nitrokey.com",

    'depends': [
        'website_sale','product'
    ],
    'data': [
        'views/product_template_view.xml',
        'views/website_sale_product.xml',
    ],

}
