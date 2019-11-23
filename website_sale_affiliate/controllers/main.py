# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from openerp.addons.website_sale.controllers.main import website_sale as Base
from openerp.http import request, route


class website_sale(Base):
    def _store_affiliate_info(self, **kwargs):
        Affiliate = request.env['sale.affiliate']
        affiliate = Affiliate.sudo().find_from_kwargs(**kwargs)
        try:
            affiliate_request = affiliate.get_request(**kwargs)
            request.session['affiliate_request'] = affiliate_request.id
        except (AttributeError, ValueError):
            pass

    @route()
    def shop(self, page=0, category=None, search='', **post):
        res = super(website_sale, self).shop(page, category,
                                            search, **post)
        self._store_affiliate_info(**post)
        return res

    @route()
    def product(self, product, category='', search='', **kwargs):
        res = super(website_sale, self).product(product, category='',
                                               search='', **kwargs)
        self._store_affiliate_info(**kwargs)
        return res
