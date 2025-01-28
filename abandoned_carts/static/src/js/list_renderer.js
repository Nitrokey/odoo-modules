odoo.define("abandoned_carts.ListRenderer", function (require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");
    ListRenderer.include({
        init: function (parent, state, params) {
            if (state.addHasSelectors) {
                params.hasSelectors = true;
            }
            return this._super(parent, state, params);
        },
    });
    setInterval(function () {
        var find_all_checkbox = $(
            document.getElementsByClassName("abandoned_data_check")
        ).find(".custom-control-input");
        var checked_checkbox = [];
        for (const checkbox in find_all_checkbox) {
            if (checkbox === "length") {
                break;
            }
            if (find_all_checkbox[checkbox].checked) {
                checked_checkbox.push(checkbox);
            }
        }
        if (checked_checkbox.length > 0) {
            $(document.getElementById("action_remove_all_customer")).hide();
            $(document.getElementById("action_remove_customer")).show();

            $(document.getElementById("action_remove_all_orders")).hide();
            $(document.getElementById("action_remove_sale_orders")).show();
        } else {
            $(document.getElementById("action_remove_all_customer")).show();
            $(document.getElementById("action_remove_customer")).hide();

            $(document.getElementById("action_remove_all_orders")).show();
            $(document.getElementById("action_remove_sale_orders")).hide();
        }
    }, 50);
});
