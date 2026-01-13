/** @odoo-module */

import {CallParticipantVideo} from "@mail/discuss/call/common/call_participant_video";
import {onWillUnmount} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(CallParticipantVideo.prototype, {
    setup() {
        super.setup(...arguments);
        this._livekit = useService("discuss.livekit");
        this._livekitRtcAdapter = useService("discuss.livekit_rtc_adapter");
        this.__livekitAttachedTrack = null;

        onWillUnmount(() => {
            try {
                if (this.__livekitAttachedTrack && this.root?.el) {
                    this.__livekitAttachedTrack.detach(this.root.el);
                }
            } catch {
                // Ignore
            }
            this.__livekitAttachedTrack = null;
        });
    },

    _update() {
        const videoEl = this.root?.el;
        if (!videoEl) {
            return;
        }

        const livekitConnected = Boolean(this._livekit?.state?.connected);
        const rtcSession = this.props.session;
        const type = this.props.type;

        // Only take over rendering for synthetic sessions (negative ids) while LiveKit is active.
        // This keeps the standard RTC UI intact for normal RTC calls.
        const isSynthetic = Boolean(
            rtcSession && typeof rtcSession.id === "number" && rtcSession.id < 0
        );
        const livekitTrack =
            livekitConnected && isSynthetic
                ? this._livekitRtcAdapter?.getLivekitVideoTrack?.(rtcSession.id, type)
                : null;

        // Detach previous LiveKit track if it no longer matches.
        if (
            this.__livekitAttachedTrack &&
            this.__livekitAttachedTrack !== livekitTrack
        ) {
            try {
                this.__livekitAttachedTrack.detach(videoEl);
            } catch {
                // Ignore
            }
            this.__livekitAttachedTrack = null;
        }

        if (livekitTrack) {
            try {
                // Let LiveKit manage element attachment so it can observe size/visibility.
                livekitTrack.attach(videoEl);
                this.__livekitAttachedTrack = livekitTrack;
                return;
            } catch {
                // Fall back to the original behavior.
                this.__livekitAttachedTrack = null;
            }
        }

        // If we previously attached a LiveKit track and now we're falling back,
        // ensure srcObject is reset by the standard code path.
        this.__livekitAttachedTrack = null;
        return super._update();
    },
});
