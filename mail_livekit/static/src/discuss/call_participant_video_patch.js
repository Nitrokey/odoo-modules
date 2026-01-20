/** @odoo-module */

import {onWillUnmount, useExternalListener} from "@odoo/owl";
import {CallParticipantVideo} from "@mail/discuss/call/common/call_participant_video";
import {patch} from "@web/core/utils/patch";

patch(CallParticipantVideo.prototype, {
    setup() {
        super.setup(...arguments);
        this.livekitTrack = null;

        // Subscribe to track rebind events
        useExternalListener(this.env.bus, "LIVEKIT:TRACK:REBIND", (event) => {
            const {sessionId, type} = event.detail;
            if (this.props.session?.id === sessionId && this.props.type === type) {
                console.log(
                    `LIVEKIT:TRACK:REBIND for session ${sessionId}, type ${type}`
                );
                this._update();
            }
        });

        onWillUnmount(() => {
            // Detach LiveKit track on unmount
            if (this.livekitTrack && this.root.el) {
                this.livekitTrack.detach(this.root.el);
            }
            this.livekitTrack = null;
        });
    },

    _update() {
        if (!this.root.el) {
            return;
        }

        const rtcSession = this.props.session;
        const type = this.props.type;

        if (!rtcSession) {
            this.root.el.srcObject = undefined;
            this.root.el.load();
            return;
        }

        // Check for LiveKit track first
        const livekitTrack = rtcSession.livekitTracks?.get(type);

        if (livekitTrack) {
            console.log(
                `Attaching LiveKit track for session ${rtcSession.id}, type ${type}`
            );

            if (this.livekitTrack && this.livekitTrack !== livekitTrack) {
                try {
                    this.livekitTrack.detach(this.root.el);
                } catch (e) {
                    console.warn("Error detaching old track:", e);
                }
            }

            // Attach new LiveKit track directly to video element
            livekitTrack.attach(this.root.el);
            this.livekitTrack = livekitTrack;

            // Don't call load() - LiveKit handles playback
        } else {
            // Fallback to standard Odoo MediaStream pattern
            if (rtcSession.getStream(type)) {
                this.root.el.srcObject = rtcSession.getStream(type);
            } else {
                this.root.el.srcObject = undefined;
            }
            this.root.el.load();
        }
    },
});
