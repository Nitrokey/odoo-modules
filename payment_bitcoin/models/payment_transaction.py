import logging
import pprint
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..controllers.bitcoin import BitcoinController

_logger = logging.getLogger(__name__)


class BitcoinPaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    duration = fields.Integer(
        string="Time Remaining", compute="_compute_time_remaining"
    )
    bitcoin_address = fields.Char()
    bitcoin_amount = fields.Float(digits=(20, 6))
    bitcoin_unit = fields.Selection(
        [
            ("BTC", "BTC"),
            ("mBTC", "mBTC"),
        ],
        "Display Unit",
    )
    bitcoin_address_link = fields.Html("Address Link", compute="_compute_link_address")

    def format_bitcoin_amount(self, amount, decimal_places=8):
        """Format the Bitcoin amount according to the partner's language."""
        lang_code = self.partner_id.lang or self.env.user.lang or "en_US"
        lang = self.env["res.lang"].search([("code", "=", lang_code)], limit=1)
        if lang:
            return lang.format(f"%.{decimal_places}f", amount, True)
        return f"{amount: .{decimal_places}f}"

    @api.depends("bitcoin_address")
    def _compute_link_address(self):
        fmt = (
            '<a target="_blank" href="https://blockchain.info/address/'
            '%s?filter=5">%s</a>'
        )
        for trn in self:
            trn.bitcoin_address_link = fmt % (trn.bitcoin_address, trn.bitcoin_address)

    def _compute_time_remaining(self):
        for transaction in self:
            if not transaction.last_state_change:
                transaction.duration = 0
                continue
            deadline = transaction.last_state_change + timedelta(
                minutes=transaction.provider_id.deadline
            )
            current_dattime = fields.Datetime.now()
            if deadline > current_dattime:
                remaining_time = deadline - fields.Datetime.now()
                transaction.duration = remaining_time.seconds
            else:
                transaction.duration = 0

    @api.model_create_multi
    def create(self, values_list):
        # values['date'] = fields.Datetime.now()
        for values in values_list:
            if values.get("provider_id"):
                provider = self.env["payment.provider"].browse(values["provider_id"])
                if provider.code != "bitcoin":
                    continue

                kwargs = {}
                sale_order_ids = values.get("sale_order_ids", [])
                if sale_order_ids:
                    kwargs["order_id"] = sale_order_ids[0][2][0]

                invoice_ids = values.get("invoice_ids", [])
                if invoice_ids:
                    kwargs["invoice_id"] = invoice_ids[0][2][0]

                if kwargs:
                    resp = self.env["bitcoin.rate"].get_rate(**kwargs)
                    if resp:
                        values["bitcoin_address"] = resp[0]
                        values["bitcoin_amount"] = resp[1]
                        values["bitcoin_unit"] = resp[2]
        return super().create(values_list)

    @api.model
    def _bitcoin_form_get_tx_from_data(self, data):
        reference = data.get("reference")
        txs = self.search([("reference", "=", reference)])

        if not txs or len(txs) > 1:
            error_msg = f"received data for reference {pprint.pformat(reference)}"
            if not txs:
                error_msg += "; no order found"
            else:
                error_msg += "; multiple order found"
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        return txs

    @api.model
    def _get_tx_from_notification_data(self, provider, data):
        tx = super()._get_tx_from_notification_data(provider, data)
        reference = data.get("reference")
        if provider != "bitcoin":
            return tx
        tx = self.search(
            [("reference", "=", reference), ("provider_code", "=", "bitcoin")]
        )
        if not tx:
            raise ValidationError(
                _(
                    "Bitcoin: " + "No transaction found matching reference %s.",
                    reference,
                )
            )
        return tx

    def _process_notification_data(self, data):
        res = super()._process_notification_data(data)

        if self.provider_code != "bitcoin":
            return res
        payment_status = data.get("state")
        if payment_status == "done":
            self._set_done()
        elif payment_status == "pending":
            self._set_pending()
        elif payment_status == "cancel":
            self._set_canceled()
        else:
            _logger.info(
                "received data with invalid payment status: %s", payment_status
            )
            self._set_error(
                _(
                    "Bitcoin: " + "Received data with invalid payment status: %s",
                    payment_status,
                )
            )

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)

        if self.provider_code != "bitcoin":
            return res
        # Only return the values actually used by the bitcoin_form template.
        # The /payment/bitcoin/feedback controller resolves the transaction via
        # `reference` alone, so no other fields are required in the POST body.
        return {
            "return_url": BitcoinController.accept_url,
            "reference": self.reference,
        }
