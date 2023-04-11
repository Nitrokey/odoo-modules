import logging
from datetime import timedelta

import werkzeug
from markupsafe import Markup

from odoo import _, http
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.fields import Command
from odoo.http import request

from odoo.addons.sale.controllers.portal import CustomerPortal, PaymentPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class BitcoinController(http.Controller):
    _accept_url = "/payment/bitcoin/feedback"

    @http.route([_accept_url], type="http", auth="public", csrf=False)
    def transfer_form_feedback(self, **post):
        post["state"] = "pending"
        tx_object = request.env["payment.transaction"].sudo()
        tx_sudo = tx_object._get_tx_from_feedback_data("bitcoin", post)
        if tx_sudo:
            tx_sudo._process_feedback_data(post)
        return request.redirect("/payment/status")

    @http.route(["/payment_bitcoin/rate"], type="json", auth="public")
    def payment_bitcoin_rate(self, order_id=False, order_ref=False):
        _logger.debug(
            "bitcoin rate lookup for Order ID %s, Order Ref %s" % (order_id, order_ref)
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


class WebsiteSale(WebsiteSale):
    def get_bitcoin_render_values(self, order, lang_id):
        if order.payment_tx_id.bitcoin_unit == "mBTC":
            bitcoin_amount = order.payment_tx_id.bitcoin_amount / 1000.0
            m_bitcoin_amount = order.payment_tx_id.bitcoin_amount
        else:
            bitcoin_amount = order.payment_tx_id.bitcoin_amount
            m_bitcoin_amount = order.payment_tx_id.bitcoin_amount * 1000.0

        uri = _("bitcoin:%(address)s$$amount=%(bt_amt)s*$message=%(msg)s") % {
            "address": order.payment_tx_id.bitcoin_address,
            "bt_amt": bitcoin_amount,
            "msg": order.name,
        }
        decimal_places = len(str(order.payment_tx_id.bitcoin_amount).split(".")[1])
        info = (
            _(
                "Please send %(amount_btc)s %(unit_btc)s (%(amount_mbtc)s %(unit_mbtc)s) \
            to the address %(address)s by %(deadline_date)s UTC."
            )
            % {
                "amount_btc": lang_id.format(
                    f"%.{decimal_places}f", bitcoin_amount, True, True
                ),
                "amount_mbtc": lang_id.format(
                    f"%.{decimal_places}f", m_bitcoin_amount, True, True
                ),
                "unit_btc": "BTC",
                "unit_mbtc": "mBTC",
                "address": order.payment_tx_id.bitcoin_address,
                "deadline_date": order.payment_tx_id.last_state_change
                + timedelta(minutes=order.payment_tx_id.acquirer_id.deadline),
            }
        )
        return (info, uri)

    @http.route(
        "/shop/payment/get_status/<int:sale_order_id>",
        type="json",
        auth="public",
        website=True,
    )
    def shop_payment_get_status(self, sale_order_id, **post):
        resp = super().shop_payment_get_status(sale_order_id=sale_order_id, **post)
        order = request.env["sale.order"].sudo().browse(sale_order_id)
        language = request.env.context.get("lang") or order.partner_id.lang or "en_US"
        lang_id = request.env["res.lang"].search([("code", "=", language)])
        if order.payment_acquirer_id.provider == "bitcoin":
            after_panel_heading = resp["message"].find(
                "</div>", resp["message"].find('<div class="card-header>')
            )
            info, uri = self.get_bitcoin_render_values(order, lang_id)
            if after_panel_heading:
                after_panel_heading += 6
                if order.get_portal_last_transaction().duration > 0:
                    msg = (
                        _(
                            """<div class="panel-body" style="padding-bottom:0px;">
                          <h4><strong>%(info)s</strong></h4>
                          </div>
                          <div class="panel-body d-flex justify-content-center \
                          align-items-center" 'style="padding-top:5px; \
                          padding-bottom:0px;">
                          <div><img class="bitcoin_barcode" src=\
                          "/report/barcode/bitcoin/?br_type=QR&amp;value=%(uri)s
                          &amp;width=300&amp;height=300"\
                          ></div>
                          <div><div class="flex-row ml-4" id="countdown_element">
                          <div><strong>Pay Within:</strong></div><div id="timecounter"\
                          class="btn btn-info cols-xs-6 "></div>
                          </div>
                          </div>
                          </div>"""
                        )
                        % {
                            "info": info,
                            "uri": uri,
                        }
                    )
                else:
                    msg = (
                        _(
                            """<div class="panel-body" style="padding-bottom:0px;">
                                <h4><strong>%(info)s</strong></h4>
                            </div>
                            <div class="panel-body d-flex justify-content-center \
                            align-items-center" 'style="padding-top:5px; \
                            padding-bottom:0px;">
                            <div><img class="bitcoin_barcode" src=\
                            "/report/barcode/bitcoin/?br_type=QR&amp;value=%(uri)s
                            &amp;width=300&amp;height=300"\
                            ></div>
                            </div>"""
                        )
                        % (
                            info,
                            uri,
                        )
                    )
                resp["message"] = Markup(msg) + resp["message"]
            else:
                resp["message"] += info
                resp["message"] += (
                    "<center>"
                    '<img src="/report/barcode/bitcoin/?br_type=QR&amp;'
                    'value=%s&amp;width=300&amp;height=300"></center>'
                ) % uri
            resp["recall"] = False
        return resp


class PaymentPortal(PaymentPortal):
    # overwrite to write the 'payment_tx_id' at transaction creation.
    @http.route("/my/orders/<int:order_id>/transaction", type="json", auth="public")
    def portal_order_transaction(self, order_id, access_token, **kwargs):
        try:
            order_sudo = self._document_check_access(
                "sale.order", order_id, access_token
            )
        except MissingError as error:
            raise error
        except AccessError:
            raise ValidationError(_("The access token is invalid.")) from AccessError

        kwargs.update(
            {
                "reference_prefix": None,
                "partner_id": order_sudo.partner_id.id,
                "sale_order_id": order_id,
            }
        )
        kwargs.pop(
            "custom_create_values", None
        )  # Don't allow passing arbitrary create values
        tx_sudo = self._create_transaction(
            custom_create_values={"sale_order_ids": [Command.set([order_id])]},
            **kwargs,
        )
        so_vals = {"payment_tx_id": tx_sudo.id}
        sale_order_id = request.env["sale.order"].browse(order_id)
        sale_order_id.sudo().write(so_vals)
        return tx_sudo._get_processing_values()


class CustomerPortal(CustomerPortal):
    @http.route(["/my/orders/<int:order_id>"], type="http", auth="public", website=True)
    def portal_order_page(
        self,
        order_id,
        report_type=None,
        access_token=None,
        message=False,
        download=False,
        **kw,
    ):
        res = super().portal_order_page(
            order_id,
            report_type=report_type,
            access_token=access_token,
            message=message,
            download=download,
            **kw,
        )
        order = request.env["sale.order"].sudo().browse(order_id)
        language = request.env.context.get("lang") or order.partner_id.lang or "en_US"
        lang_id = request.env["res.lang"].search([("code", "=", language)])
        if order.payment_acquirer_id.provider == "bitcoin":
            info, uri = WebsiteSale.get_bitcoin_render_values(self, order, lang_id)
            res.qcontext.update({"uri": uri, "info": info})
        return res
