# -*- coding: utf-8 -*-
from odoo import fields, models


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    user_ids = fields.Many2many('res.users', 'warehouse_user_rel',
                                'warehouse_id', 'user_id', 'Users')
