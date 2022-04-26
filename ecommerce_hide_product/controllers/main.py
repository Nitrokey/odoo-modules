# -*- coding: utf-8 -*-

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    def _get_search_domain(self, search, category, attrib_values):

        domain = super(WebsiteSale, self)._get_search_domain(search=search, category=category,attrib_values=attrib_values)
        domain += [('hide_accessory_product', '!=', True)]
        return domain