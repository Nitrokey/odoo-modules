# -*- coding: utf-8 -*-
{
    'name': 'Partner Activity Overview',
    'author': 'ERP Harbor Consulting Services',
    'category': 'Sales',
    'summary': 'Partner Activity Overview',
    'website': 'http://www.erpharbor.com',
    'version': '12.0.1.0.0',
    'description': """
        Post the messages of different different objects (Sale, Purchase, Invoice, Lead, etc.) into the related partner's chatter box.
    """,
    'depends': [
        'sale_crm', 'purchase_stock', 'nitrokey_helpdesk_mgmt', 'calendar', 'crm_phonecall',
    ],
    'license': 'AGPL-3',
    'installable': True,
}
