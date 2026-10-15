from odoo import fields, models


class BitcoinPaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("bitcoin", "Bitcoin")], ondelete={"bitcoin": "set default"}
    )
    deadline = fields.Float(
        help="Add a deadline to Bitcoin payments within which the payment should "
        "be made.",
    )
    bitcoin_order_older_than = fields.Integer(
        "Hours",
        help="Address check for orders which are not older than",
        default=6,
    )
    bitcoin_send_email = fields.Boolean(default=False)
