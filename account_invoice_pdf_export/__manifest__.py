# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2022 initOS GmbH
#
##############################################################################
{
    'name': "Export Invoices",
    'description': """Export multiple invoices PDF in Zip 
    Allows User To Select From Date and To Date For Export Invoices in ZIP Format For Selected Invoice status.
    For this Go To The Invoice > Click On Reporting Menu > Select the Export Invoices.
    """,
    'category': '',
    'version': '15.0.1.0.0',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/invoice_pdf_export_view.xml',
    ],
    'author': "Nitrokey GmbH",
    'license': 'AGPL-3',
    'website': "http://www.nitrokey.com",
}
