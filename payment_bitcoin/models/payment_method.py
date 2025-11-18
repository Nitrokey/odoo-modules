from odoo import api, models


class PaymentMethod(models.Model):
    _inherit = "payment.method"

    @api.model
    def _get_compatible_payment_methods(
        self,
        provider_ids,
        partner_id,
        currency_id=None,
        force_tokenization=False,
        is_express_checkout=False,
        report=None,
        **kwargs,
    ):
        """
        Override to hide Bitcoin payment methods when no Bitcoin
        addresses are available.
        """
        res = super()._get_compatible_payment_methods(
            provider_ids,
            partner_id,
            currency_id,
            force_tokenization,
            is_express_checkout,
            report,
            **kwargs,
        )

        bitcoin_method = res.filtered(lambda m: m.code == "bitcoin")
        if bitcoin_method:
            bitcoin_address = self.env["bitcoin.address"].search(
                [("order_id", "=", False), ("invoice_id", "=", False)], limit=1
            )
            if not bitcoin_address:
                res -= bitcoin_method

        return res
