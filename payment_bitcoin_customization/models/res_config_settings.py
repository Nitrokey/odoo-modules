from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bit_coin_order_older_than = fields.Integer(
        'Hours',
        help='Addresses checking for orders which are not older than.'
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'bit_coin_order_older_than': safe_eval(
                self.env['ir.config_parameter'].get_param(
                    'payment_bitcoin.bit_coin_order_older_than', '6')),
        })
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'payment_bitcoin.bit_coin_order_older_than',
            repr(self.bit_coin_order_older_than))
