from odoo import http
from odoo.http import request

from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.sale.controllers.portal import CustomerPortal

from .bitcoin import get_bitcoin_render_values


class CustomerPortalBitcoin(CustomerPortal):
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
        last_transaction = order.transaction_ids[-1]
        if last_transaction and last_transaction.provider_code == "bitcoin":
            lang_code = (
                request.env.context.get("lang") or order.partner_id.lang or "en_US"
            )
            lang = request.env["res.lang"].search([("code", "=", lang_code)])
            info, uri = get_bitcoin_render_values(
                last_transaction, lang=lang, order=order
            )
            res.qcontext.update({"uri": uri, "info": info})
        return res


class PortalAccountBitcoin(PortalAccount):
    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        res = super()._invoice_get_page_view_values(invoice, access_token, **kwargs)
        invoice = res.get("invoice")
        if not invoice:
            return res

        transaction = invoice.transaction_ids.filtered_domain(
            [("provider_code", "=", "bitcoin"), ("state", "=", "pending")]
        )[:1]
        if transaction:
            lang_code = (
                request.env.context.get("lang") or invoice.partner_id.lang or "en_US"
            )
            lang = request.env["res.lang"].search([("code", "=", lang_code)])
            info, uri = get_bitcoin_render_values(
                transaction, lang=lang, invoice=invoice
            )
            res.update({"uri": uri, "info": info})
        return res
