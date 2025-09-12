/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {rpc} from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

// In Odoo 18, the frontend payment form widget is PaymentForm in the publicWidget registry.
// We extend it to hook into the payment option selection and validate Bitcoin availability.

const BitcoinMixin = {
    async _selectPaymentOption(ev) {
        // Call super first to keep standard behavior (expand forms, toggle button, etc.).
        await this._super(...arguments);
        const target = ev?.target || ev?.currentTarget || this.el;
        const provider =
            target?.dataset?.providerCode ||
            target.closest("[data-provider]")?.dataset?.providerCode ||
            this.el.querySelector('input[name="o_payment_radio"]:checked')?.dataset
                ?.providerCode;
        if (provider !== "bitcoin") {
            return;
        }
        // Try to get order identifiers from the DOM similar to the legacy behavior.
        const orderId =
            document
                .querySelector(
                    'span[data-oe-model="sale.order"][data-oe-field="amount_total"]'
                )
                ?.getAttribute("data-oe-id") ||
            document
                .querySelector(
                    'b[data-oe-model="sale.order"][data-oe-field="amount_total"]'
                )
                ?.getAttribute("data-oe-id") ||
            document
                .querySelector("table#sales_order_table")
                ?.getAttribute("data-order-id");
        const orderRef =
            document.querySelector('input[name="reference"]')?.value || undefined;

        try {
            const data = await rpc("/payment_bitcoin/rate", {
                order_id: orderId,
                order_ref: orderRef,
            });
            if (data === false) {
                // Inform the user and unselect/disable the option.
                // eslint-disable-next-line no-alert
                alert(_t("Payment method Bitcoin is currently unavailable."));
                const radio = target.matches('input[name="o_payment_radio"]')
                    ? target
                    : target.querySelector('input[name="o_payment_radio"]');
                if (radio) {
                    radio.disabled = true;
                    radio.checked = false;
                }
                // Trigger a button update.
                this._enableButton(false);
            }
        } catch (e) {
            // In case of RPC failure, silently ignore to not block other providers.
            // Console error is acceptable for debugging.
            // eslint-disable-next-line no-console
            console.error("Bitcoin availability check failed", e);
        }
    },
};

publicWidget.registry.PaymentForm.include(BitcoinMixin);

export default BitcoinMixin;
