# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleDeliveryBlockReason(models.Model):
    _inherit = "sale.delivery.block.reason"

    remove_on_payment = fields.Boolean(
        "Remove Block on Payment",
        help="If checked, this delivery block will be automatically removed "
        "when the invoice is paid",
    )
