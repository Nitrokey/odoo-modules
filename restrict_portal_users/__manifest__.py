# -*- coding: utf-8 -*-
{
    'name': "Restrict Portal Users",

    'summary': """
        Restrict the portal user""",

    'description': """
       When user do following action in odoo, it only shows internal users contacts in dropdown.
            Chatter mentioning (@username)
            Project task assignment
            Helpdesk ticket assignments
            Sales order assignments (Salesperson)
            Invoicing, Salesperson
            Purchase Representative
            Manufacturing Responsible

    """,

    # Author

    'author': "Nitrokey GmbH",
    'license': 'AGPL-3',
    'website': "https://www.nitrokey.com",

    'version': '12.0.1.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase', 'sale_management', 'helpdesk_mgmt', 'project','mrp'],

    # always loaded
    'data': [
        'views/purchase_order.xml',
        'views/account_invoice.xml',
        'views/mrp_production.xml',
        'views/sale_order.xml',
        'views/helpdesk_ticket.xml',
        'views/project_task.xml',
    ],

}
