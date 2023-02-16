from odoo import models


class MrpImmediateProduction(models.TransientModel):
    _inherit = "mrp.immediate.production"
    _description = "Immediate Production"

    def process(self):
        res = super().process()
        ctx = self._context.copy()
        active_id = ctx.get("active_id")
        model_name = ctx.get("active_model")
        if model_name == "mrp.production" and active_id:
            model_obj = self.env[model_name].browse(active_id)
            if model_obj.product_id.is_automatically:
                model_obj.product_id.button_bom_cost()
        return res
