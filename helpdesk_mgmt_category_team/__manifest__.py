# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2022 initOS GmbH
#
##############################################################################
{
    'name': "Helpdesk Management Team",
    'description': """
User will set Team in Helpdesk Category. Based on that, when user create ticket from portal and select category, system auto set Team from the selected category in Ticket.

    """,
    'category': '',
    'version': '12.0.1.0',
    'depends': [
        'helpdesk_mgmt',
    ],
    'data': [
        'views/helpdesk_ticket_category.xml',
        
    ],
    'author': "Nitrokey GmbH",
    'license': 'AGPL-3',
    'website': "http://www.initos.com",
}