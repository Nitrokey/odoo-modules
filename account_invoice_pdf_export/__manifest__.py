# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 initOS GmbH
#
##############################################################################
{
    'name': "Export Invoices",
    'description': """Export multiple invoices PDF in Zip 
    """,
    'category': '',
    'version': '1.3',
    'depends': [
        'account',
    ],
    'data': [
        'views/templates.xml',
        'wizard/invoice_pdf_export_view.xml',
        
    ],
    'author': "Nitrokey GmbH",
    'license': 'AGPL-3',
    'website': "http://www.initos.com",
}
