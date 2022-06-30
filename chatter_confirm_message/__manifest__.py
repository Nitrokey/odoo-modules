{
    "name": "Chatter Confirm Message",
    "version": "12.0.1",
    "summary": "Chatter confirm message",
    "description": """
This module will show confirmation dialog while sending message from chatter when any one follower of the record is not internal user.
    """,
    # Author
    'author': "Nitrokey GmbH",
    'website': "http://www.nitrokey.com",
    'maintainer': 'Nitrokey GmbH',

    "depends": ["mail", 'base'],
    "data": [
        'views/template.xml',
    ],
    "installable": True,
}
