# -*- coding: utf-8 -*-
# Copyright 2017 initOS GmbH. <http://www.initos.com>
# Copyright 2017 GYB IT SOLUTIONS <http://www.gybitsolutions.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields

class WebsiteMenu(models.Model):
    _inherit = "website.menu"

    url = fields.Char(string='Url',
                      translate=True)

class WebsitePage(models.Model):
    _inherit = "website.page"

    url = fields.Char('Page URL', translate=True)
