odoo.define("payment_bitcoin.bitcoin", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var core = require("web.core");
    var _t = core._t;
    const checkoutForm = require("payment.checkout_form");
    const manageForm = require("payment.manage_form");

    const BitcoinMixin = {
        _onClickPaymentOption: function (ev) {
            var $order_id =
                $(
                    'span[data-oe-model="sale.order"][data-oe-field="amount_total"]'
                ).attr("data-oe-id") ||
                $('b[data-oe-model="sale.order"][data-oe-field="amount_total"]').attr(
                    "data-oe-id"
                ) ||
                $("table#sales_order_table").attr("data-order-id");
            var $order_ref = $('input[name="reference"]').val();
            var provider = $(ev.currentTarget)
                .find('input[name="o_payment_radio"]')
                .data("provider");
            if (provider === "bitcoin") {
                ajax.jsonRpc("/payment_bitcoin/rate", "call", {
                    order_id: $order_id,
                    order_ref: $order_ref,
                }).then(function (data) {
                    if (data === false) {
                        alert(_t("Payment method Bitcoin is currently unavailable."));
                        $(ev.currentTarget)
                            .find('input[name="o_payment_radio"]')
                            .attr("disabled", "disabled");
                        $(ev.currentTarget)
                            .find('input[name="o_payment_radio"]')
                            .prop("checked", false);
                    }
                });
            }
            return this._super(...arguments);
        },
    };
    checkoutForm.include(BitcoinMixin);
    manageForm.include(BitcoinMixin);
});
