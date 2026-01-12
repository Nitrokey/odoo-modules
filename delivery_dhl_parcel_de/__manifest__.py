# -*- coding: utf-8 -*-pack
{

    # App information
    'name': 'DHL Parcel(Post & Parcel Germany) DE Shipping Integration',
    'category': 'Website',
    'version': '18.0.1.0.0',
    'summary': """Using DHL Parcel DE Easily manage Shipping Operation in odoo.Export Order While Validate Delivery Order.Import Tracking From DHL Parcel DE to odoo.Generate Label in odoo.We also Provide the ups,fedex,dhl express shipping integration.""",
    'license': 'AGPL-3',

    # Dependencies
    'depends': ['delivery', 'base_iso3166', 'nitrokey_delivery', "stock_picking_declared_value"],

    # Views
    'data': [
        'view/res_company.xml',
        'view/delivery_carrier.xml',
    ],
    # Odoo Store Specific
    'images': ['static/description/cover.jpeg'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_dhl_parcel_de_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '99',
    'currency': 'EUR',

}
# version changelog
