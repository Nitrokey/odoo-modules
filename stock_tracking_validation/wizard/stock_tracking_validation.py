# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class StockTrackingValidation(models.TransientModel):
    _name = 'stock.tracking.validation'
    _description = 'Stock tracking validation'

    product_data = fields.Text()

    def confirm_stock_tracking_validate(self):
        active_id = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_model == 'mrp.product.produce':
            mrp_production = self.env['mrp.product.produce'].sudo().browse(active_id).do_produce()
        else:
            stock_picking = self.env['stock.picking'].sudo().browse(active_id)
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in stock_picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            if no_quantities_done:
                wizard_transfer = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, stock_picking.id)]})
                return wizard_transfer.process()
            if stock_picking._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
                wizard_transfer = self.env['stock.overprocessed.transfer'].create({'picking_id': stock_picking.id})
                return wizard_transfer.action_confirm()
            if stock_picking._check_backorder():
                return stock_picking.action_generate_backorder_wizard()
            return stock_picking.button_validate()