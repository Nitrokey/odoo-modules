from odoo import fields, models


class StockTrackingValidation(models.TransientModel):
    _name = "stock.tracking.validation"
    _description = "Stock tracking validation"

    product_data = fields.Html()

    def confirm_stock_tracking_validate(self):
        active_id = self.env.context.get("active_ids")
        active_model = self.env.context.get("active_model")
        if active_model == "mrp.production":
            mrp_production = self.env["mrp.production"].sudo().browse(active_id)
            return mrp_production.button_mark_done()
        else:
            stock_picking = self.env["stock.picking"].sudo().browse(active_id)
            return stock_picking.button_validate()
