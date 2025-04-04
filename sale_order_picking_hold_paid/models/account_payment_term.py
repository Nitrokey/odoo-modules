# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    hold_picking_until_paid = fields.Boolean(
        help="If checked, delivery orders will be held until the invoice is fully paid",
        default=False,
    )
