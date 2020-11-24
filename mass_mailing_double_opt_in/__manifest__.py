# -*- coding: utf-8 -*-
{
    'name': 'Mass Mailing Double opt-in',
    'version': '12.0.1.0.0',
    'category': 'Website',
    'author': 'ERP Harbor Consulting Services',
    'website': 'http://www.erpharbor.com',
    'summary': 'Mass Mailing Double opt-in',
    'description': """
Mass Mailing Double opt-in
     """,
    'depends': [
        'website_mass_mailing',
    ],
    'data': [
        'security/mass_mailing_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/newsletter.xml',
        'views/mass_mailing_view.xml',
        'views/invalid_confirmation.xml',
        'views/unsubscribe_templates.xml',
    ],
    'installable': True,
}
