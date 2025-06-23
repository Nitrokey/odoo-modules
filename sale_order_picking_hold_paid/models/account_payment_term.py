# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    delivery_block_reason_id = fields.Many2one(
        "sale.delivery.block.reason",
        string="Delivery Block Reason",
        help="Select a delivery block reason that will be applied to orders using "
        "this payment term. Orders will be held until the invoice is fully paid.",
    )

    def get_delivery_block_reason(self):
        """Get the delivery block reason for this payment term."""
        return self.delivery_block_reason_id
