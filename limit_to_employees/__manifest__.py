{
    "name": "Limit To Employees",
    "summary": """
When user do following action in odoo, it only shows internal users contacts in dropdown.
  * Chatter mentioning (@username)
  * Helpdesk ticket assignments
  * Invoicing, Salesperson
    """,
    # Author
    "author": "Nitrokey GmbH",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-tools",
    "version": "15.0.1.1.0",
    # any module necessary for this one to work correctly
    "depends": ["helpdesk_mgmt", "account"],
    # always loaded
    "data": [
        "views/account_invoice.xml",
    ],
}
