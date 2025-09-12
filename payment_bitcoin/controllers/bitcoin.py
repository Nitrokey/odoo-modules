import logging
from datetime import timedelta

import werkzeug

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


def get_bitcoin_render_values(transaction, lang, order=None, invoice=None):
    if transaction.bitcoin_unit == "mBTC":
        bitcoin_amount = transaction.bitcoin_amount / 1000.0
        m_bitcoin_amount = transaction.bitcoin_amount
    else:
        bitcoin_amount = transaction.bitcoin_amount
        m_bitcoin_amount = transaction.bitcoin_amount * 1000.0

    if order:
        message = order.name
    elif invoice:
        message = invoice.name
    else:
        message = "Bitcoin Payment"

    uri = _("bitcoin:%(address)s$$amount=%(bt_amt)s*$message=%(msg)s") % {
        "address": transaction.bitcoin_address,
        "bt_amt": bitcoin_amount,
        "msg": message,
    }
    decimal_places = len(str(transaction.bitcoin_amount).split(".")[1])
    info = _(
        "Please send %(amount_btc)s %(unit_btc)s (%(amount_mbtc)s %(unit_mbtc)s) \
        to the address %(address)s by %(deadline_date)s UTC."
    ) % {
        "amount_btc": lang.format(f"%.{decimal_places}f", bitcoin_amount, True),
        "amount_mbtc": lang.format(f"%.{decimal_places}f", m_bitcoin_amount, True),
        "unit_btc": "BTC",
        "unit_mbtc": "mBTC",
        "address": transaction.bitcoin_address,
        "deadline_date": transaction.last_state_change
        + timedelta(minutes=transaction.provider_id.deadline),
    }
    return info, uri


class BitcoinController(http.Controller):
    accept_url = "/payment/bitcoin/feedback"

    @http.route([accept_url], type="http", auth="public", csrf=False)
    def transfer_form_feedback(self, **post):
        post["state"] = "pending"
        tx_object = request.env["payment.transaction"].sudo()
        tx_sudo = tx_object._get_tx_from_notification_data("bitcoin", post)
        if tx_sudo:
            tx_sudo._process_notification_data(post)
        return request.redirect("/payment/status")

    @http.route(["/payment_bitcoin/rate"], type="json", auth="public")
    def payment_bitcoin_rate(self, order_id=False, order_ref=False):
        _logger.debug(
            f"bitcoin rate lookup for Order ID {order_id}, Order Ref {order_ref}"
        )
        return request.env["bitcoin.rate"].sudo().get_rate(order_id, order_ref)

    @http.route(
        ["/report/barcode/bitcoin", "/report/barcode/bitcoin/<br_type>/<path:value>"],
        type="http",
        auth="public",
    )
    def report_barcode_bitcoin(
        self, br_type, value, width=600, height=100, humanreadable=0
    ):
        """Contoller able to render barcode images thanks to reportlab.
        Samples:
          <img t-att-src="'/report/barcode/QR/%s' % o.name"/>
          <img t-att-src="'/report/barcode/?type=%s&amp;value=%s&amp;
            width=%s&amp;height=%s' % ('QR', o.name, 200, 200)"/>

        :param type: Accepted types: 'Codabar', 'Code11', 'Code128',
        'EAN13', 'EAN8', 'Extended39', 'Extended93', 'FIM', 'I2of5', 'MSI',
        'POSTNET', 'QR', 'Standard39', 'Standard93', 'UPCA', 'USPS_4State'
        :param humanreadable: Accepted values: 0 (default) or 1.
        1 will insert the readable value
        at the bottom of the output image
        """
        try:
            for rplce in (("$$", "?"), ("*$", "&")):
                value = value.replace(*rplce)
            barcode = request.env["ir.actions.report"].barcode(
                br_type, value, width=width, height=height, humanreadable=humanreadable
            )
        except (ValueError, AttributeError) as exc:
            raise werkzeug.exceptions.HTTPException(
                description="Cannot convert into barcode."
            ) from exc
        return request.make_response(barcode, headers=[("Content-Type", "image/png")])
