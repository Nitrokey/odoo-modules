odoo.define("payment_bitcoin.duration", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.reloadDuration = publicWidget.Widget.extend({
        selector: ".oe_website_sale_tx_status, #quote_content",
        init: function () {
            this._super.apply(this, arguments);
            this._updateSeconds();
        },
        _updateSeconds: function () {
            var seconds = $(".total_duration_seconds").text();
            var interval = setInterval(function () {
                $("#timecounter").css("font-size", "60px");
                var seconds1 = seconds - 1;
                seconds = Number(seconds1);
                var h = Math.floor(seconds / 3600);
                var m = Math.floor(((seconds / 3600) % 1).toFixed(4) * 60);
                var s = parseInt(
                    (
                        (((seconds / 3600) % 1).toFixed(4) * 60 -
                            Math.floor(((seconds / 3600) % 1).toFixed(4) * 60)) *
                        60
                    ).toFixed(),
                    10
                );

                var hDisplay = h >= 0 ? String(("0" + h).slice(-2)) + "" : "";
                var mDisplay = m >= 0 ? String(("0" + m).slice(-2)) + "" : "";
                var sDisplay = s >= 0 ? String(("0" + s).slice(-2)) + "" : "";

                seconds = seconds1;
                if (seconds <= 0) {
                    clearInterval(interval);
                }
                if (seconds >= 0) {
                    $("div#timecounter").html(
                        hDisplay + ":" + mDisplay + ":" + sDisplay
                    );
                }
            }, 1000);
        },
    });
    return publicWidget.registry.reloadDuration;
});
