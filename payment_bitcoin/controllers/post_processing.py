from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

from .bitcoin import get_bitcoin_render_values


class PaymentPostProcessingBitcoin(PaymentPostProcessing):
    @http.route()
    def display_status(self, **kwargs):
        """Inherited to add Bitcoin-specific information."""
        monitored_tx = self._get_monitored_transaction()
        # The session might have expired, or the transaction never existed.
        values = {"tx": monitored_tx} if monitored_tx else {"payment_not_found": True}

        if monitored_tx and monitored_tx.provider_code == "bitcoin":
            order = (
                monitored_tx.sale_order_ids[0] if monitored_tx.sale_order_ids else None
            )
            lang_code = (
                request.env.context.get("lang") or order.partner_id.lang or "en_US"
            )
            lang = request.env["res.lang"].search([("code", "=", lang_code)])
            info, uri = get_bitcoin_render_values(monitored_tx, lang=lang, order=order)
            values.update({"info": info, "uri": uri})

        return request.render("payment.payment_status", values)
