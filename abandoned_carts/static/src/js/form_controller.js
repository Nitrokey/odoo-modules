odoo.define("abandoned_carts.FormController", function (require) {
    "use strict";

    var FormController = require("web.FormController");

    FormController.include({
        _callButtonAction: function (attrs, record) {
            if (
                this.modelName === "customer.wizard" &&
                attrs.name === "action_remove_customer_manual"
            ) {
                var ctx = attrs.context || {};
                var $selectedRows = this.$(
                    "tbody .o_list_record_selector input:checked"
                ).closest("tr");
                var selected_ids = _.map($selectedRows, function (row) {
                    return $(row).data("id");
                });
                _.map(this.initialState.data.customer_ids.data, function (row) {
                    return row.id;
                });

                var records = this.initialState.data.customer_ids.data.filter(function (
                    row
                ) {
                    return selected_ids.indexOf(row.id) >= 0;
                });
                ctx.deleting_ids = _.map(records, function (rec) {
                    return rec.res_id;
                });
                attrs.context = ctx;
            }
            if (
                this.modelName === "sale.order.wizard" &&
                attrs.name === "action_remove_sale_order_manual"
            ) {
                var ctx_sow = attrs.context || {};
                var $selectedRows_sow = this.$(
                    "tbody .o_list_record_selector input:checked"
                ).closest("tr");
                var selected_ids_sow = _.map($selectedRows_sow, function (row) {
                    return $(row).data("id");
                });
                _.map(this.initialState.data.sale_order_ids.data, function (row) {
                    return row.id;
                });

                var records_sow = this.initialState.data.sale_order_ids.data.filter(
                    function (row) {
                        return selected_ids_sow.indexOf(row.id) >= 0;
                    }
                );
                ctx_sow.deleting_ids = _.map(records_sow, function (rec) {
                    return rec.res_id;
                });
                attrs.context = ctx_sow;
            }
            return this._super(attrs, record);
        },
    });
});
