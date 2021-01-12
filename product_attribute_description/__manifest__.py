# -*- coding: utf-8 -*-
{
    'name': 'Product Attribute Description',
    'version': '12.0.1.0.0',
    'category': 'Website',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Product Attribute Description',
    'description': """
This module adds the information icon next to the attribute name in the website and display the related description on mouse hover.
     """,
    'depends': [
        'sale',
    ],
    'data': [
        'views/product_attribute_view.xml',
        'views/template.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
}
