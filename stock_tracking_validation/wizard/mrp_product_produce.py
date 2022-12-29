# -*- coding: utf-8 -*-
from odoo import models

class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def open_stock_tracking_wizard(self):
        produce_line_has_lot = self.produce_line_ids.filtered(lambda m : m.lot_id)
        if not produce_line_has_lot:
            return self.do_produce()
        action = self.env.ref('stock_tracking_validation.action_product_stock_validation').read()[0]
        product_data = '''<table class="table table-sm w-50 table-bordered table-striped table-hover m-2"><tr>
                            <thead class="class="thead-light"">
                                <tr>
                                    <th>Product Name</th>
                                    <th>Lot/Serial</th>
                                </tr>
                            </thead>
                            <tbody>'''
        for produce_line in self.produce_line_ids.filtered(lambda m : m.lot_id):
            name = produce_line.product_id.name
            lot = produce_line.lot_id.name
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