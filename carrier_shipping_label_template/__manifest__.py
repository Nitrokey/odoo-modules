{
 'name': 'Carrier shipping label template',
 'summary': 'Print shipping label from print menu',
 'version': '12.0.3.1.5',
 'author': "Nitrokey GmbH",
 'license': 'AGPL-3',
 'depends': [
     'nitrokey_ups_delivery_carrier',
     'carrier_deutsche_post',

 ],
 'data': [
     "views/report_ups.xml",
     'views/report_deutsch_post.xml',
 ],
 'auto_install': False,
 'installable': True,
 }
