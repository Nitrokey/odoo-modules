# -*- coding: utf-8 -*-
{
    'name': 'Add Up Pricelist Discounts',
    'version': '12.0.1.0.0',
    'category': 'Sale',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Add Up Pricelist Discounts',
    'description': """
* Combine the discount amount based on the selected Pricelist and Base Pricelist to calculate the discount price.
Ex: Selected pricelist has 25% discount and base pricelist has 20% discount, so total discount would be 45%
     """,
    'depends': [
        'product',
    ],
    'data': [
        'views/product_pricelist_view.xml',
    ],
    'installable': True,
}
