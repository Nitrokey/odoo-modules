# -*- coding: utf-8 -*-

import logging
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)

class WebsiteSaleFirstLastname(WebsiteSale):
    def values_postprocess(self, order, mode, values, errors, error_msg):
        last_name = values.get('last_name')
        if last_name:
            values['name'] = values['name']+' '+last_name
        company_type = values.get('company_type')
        new_values, errors, error_msg = super(WebsiteSaleFirstLastname, self).values_postprocess(order, mode, values, errors, error_msg)
        if company_type:
            new_values['company_type'] = company_type
        return new_values, errors, error_msg
    