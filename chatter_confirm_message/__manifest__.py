{
    "name": "Chatter Confirm Message",
    "version": "15.0.1.0.0",
    "summary": """
This module will show confirmation dialog while sending message from chatter when any one follower of the record is not internal user.
    """,
    # Author
    'author': "Nitrokey GmbH",
    'website': "http://www.nitrokey.com",
    'maintainer': 'Nitrokey GmbH',

    "depends": ["mail", 'base'],
    "data": [

    ],
    "installable": True,
    'assets': {
        'web.assets_backend': [
            ('replace', 'mail/static/src/components/composer/composer.js',
             'chatter_confirm_message/static/src/components/composer/composer.js'),

        ],

    }
}
