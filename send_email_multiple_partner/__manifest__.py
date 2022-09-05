{
    "name": "Send email to multiple partners at once",
    "category": "Nitrokey",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
    Send email to multiple partners at once
Send custom emails to multiple partners at once from Contacts view,
Sales view, and Inventory view. Select records in list view, than click Send Email menu
inside Action button, a dialogue window will open. There user writes email and clicks
on Send button to send that email to all selected contacts/Sales/Inventory, The sent
emails are listed/documented in the history for each particular order.
        """,
    "author": "initOS",
    "website": "https://github.com/OCA/server-tools",
    "depends": ["sale_stock"],
    "data": [
        "views/sale_order_view.xml",
        "views/res_partner_view.xml",
        "views/stock_view.xml",
    ],
    "installable": True,
    "application": False,
}
