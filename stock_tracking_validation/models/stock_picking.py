# -*- coding: utf-8 -*-
from odoo import models

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def open_stock_tracking_wizard(self):
        action = self.env.ref('stock_tracking_validation.action_product_stock_validation').read()[0]
        product_data = '''<table class="table table-sm w-50 table-bordered table-striped table-hover m-2"><tr>
                            <thead class="class="thead-light"">
                                <tr>
                                    <th>Product Name</th>
                                    <th>Lot/Serial</th>
                                </tr>
                            </thead>
                            <tbody>'''
        for produce_line in self.move_ids_without_package:
            name = produce_line.product_id.name
            lot = produce_line.active_move_line_ids.mapped('lot_id').name
            product_data +="""
                <tr>
                    <td class="border">%s</td>
                    <td>%s</td>
                </tr>
            """% (name, lot)
        product_data += '''
                        </tbody>
                        </table>
                        '''
        action['context'] = {'default_product_data': product_data}
        return action