// @odoo-module

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.reloadDuration = publicWidget.Widget.extend({
    selector: "#countdown_element, #quote_content",

    init() {
        this._super(...arguments);
        this._interval = null;
        this._updateSeconds();
    },

    destroy() {
        if (this._interval) {
            clearInterval(this._interval);
            this._interval = null;
        }
        this._super(...arguments);
    },

    _updateSeconds() {
        const secondsNode = document.querySelector(".total_duration_seconds");
        let seconds = secondsNode ? parseInt(secondsNode.textContent || "0", 10) : 0;
        const timeCounter = document.getElementById("timecounter");
        if (!timeCounter) {
            // Nothing to update.
            return;
        }
        timeCounter.style.fontSize = "60px";

        const tick = () => {
            const s1 = seconds - 1;
            seconds = Number(s1);
            const h = Math.floor(seconds / 3600);
            const m = Math.floor(((seconds / 3600) % 1).toFixed(4) * 60);
            // Parse seconds with base 10
            const s = parseInt(
                (
                    (((seconds / 3600) % 1).toFixed(4) * 60 -
                        Math.floor(((seconds / 3600) % 1).toFixed(4) * 60)) *
                    60
                ).toFixed(),
                10
            );

            const hDisplay = h >= 0 ? String(("0" + h).slice(-2)) : "";
            const mDisplay = m >= 0 ? String(("0" + m).slice(-2)) : "";
            const sDisplay = s >= 0 ? String(("0" + s).slice(-2)) : "";

            seconds = s1;
            if (seconds <= 0) {
                clearInterval(this._interval);
                this._interval = null;
            }
            if (seconds >= 0) {
                timeCounter.innerHTML = `${hDisplay}:${mDisplay}:${sDisplay}`;
            }
        };

        this._interval = setInterval(tick, 1000);
    },
});

export default publicWidget.registry.reloadDuration;
