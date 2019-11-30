# -*- coding: utf-8 -*-

{
    'name': "Abandoned Carts",
    'description': 'System will automatically delete website Quotations when those are older than X days.',
    'category': '',
    'version': '1.0',
    'depends': ['website_sale','crm','account','project', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_view.xml',
        'views/removed_record_log_view.xml',
        'wizard/sale_order_view.xml',
        'wizard/customer_view.xml',
        
    ],
    'author': "Nilesh Sheliya",
    'website': "",
    
}