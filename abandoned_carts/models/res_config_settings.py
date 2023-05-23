from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleConfigSettings(models.TransientModel):
    """You can set here the retention period and the maximum delete limit"""

    _inherit = "res.config.settings"

    order_retention_period = fields.Integer(
        "Order older than X hours",
        default=48,
        help="Retention period for order. After X hours order are deleted automatically.",
    )
    max_delete_batch_limit = fields.Integer(
        "Maximum record Delete limit",
        default=2000,
        help="User can delete maximum x records(Quotation/Customer) \
        at a time.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            {
                "order_retention_period": safe_eval(
                    self.env["ir.config_parameter"].get_param(
                        "abandoned_carts" ".order_retention_period", "48"
                    )
                ),
                "max_delete_batch_limit": safe_eval(
                    self.env["ir.config_parameter"].get_param(
                        "abandoned_carts" ".max_delete_batch_limit", "2000"
                    )
                ),
            }
        )
        return res

    def set_values(self):
        res = super().set_values()
        self.env["ir.config_parameter"].set_param(
            "abandoned_carts.order_retention_period", repr(self.order_retention_period)
        )
        self.env["ir.config_parameter"].set_param(
            "abandoned_carts.max_delete_batch_limit", repr(self.max_delete_batch_limit)
        )
        return res
