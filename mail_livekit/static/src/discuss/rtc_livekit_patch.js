/** @odoo-module */
import {CONNECTION_TYPES, Rtc, rtcService} from "@mail/discuss/call/common/rtc_service";
import {LiveKitAdapter} from "./livekit_adapter";
import {PeerToPeer} from "@mail/discuss/call/common/peer_to_peer";
import {RtcSession} from "@mail/discuss/call/common/rtc_session_model";
import {Source} from "./livekit_service";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {patch} from "@web/core/utils/patch";

patch(RtcSession.prototype, {
    livekit_token: undefined,
    livekit_room_name: undefined,
    livekit_url: undefined,

    setup() {
        super.setup(...arguments);
        // Store LiveKit tracks separately from MediaStreams
        this.livekitTracks = new Map();
    },
});

patch(PeerToPeer.prototype, {
    async handleNotification() {
        console.log("message intercepted");
    },

    _dataChannelupdateInBroadcast() {
        console.log("message intercepted");
    },
});

patch(Rtc.prototype, {
    start() {
        super.start();
        browser.addEventListener("pagehide", () => {
            if (this.state.channel) {
                const data = JSON.stringify({
                    params: {channel_id: this.state.channel.id},
                });
                const blob = new Blob([data], {type: "application/json"});
                browser.navigator.sendBeacon("/mail/rtc/channel/leave_call", blob);
                this.network?.disconnect();
            }
        });
    },

    async _initConnection() {
        this.selfSession.connectionState = "selecting network type";
        this.network?.disconnect();
        this.network = new LiveKitAdapter();
        this.state.connectionType = CONNECTION_TYPES.SERVER;

        this.network.addEventListener("update", (event) => {
            try {
                this._handleNetworkUpdates(event);
            } catch (error) {
                if (!error.message?.includes("closed")) {
                    console.error("Error in network update:", error);
                }
            }
        });
        this.network.addEventListener("updateTrack", async (event) => {
            if (event.detail.name === "trackSubscribed") {
                const {sessionId, type, track} = event.detail.payload;
                console.log(
                    `Track subscribed for session ${sessionId}, type ${type}. Triggering rebind.`
                );
                const rtcSession = await this.store.RtcSession.getWhenReady(sessionId);

                // Store LiveKit track separately
                rtcSession.livekitTracks.set(type, track);

                // Create dummy MediaStream for UI rendering (hasVideo check)
                const dummyStream = new window.MediaStream();
                rtcSession.videoStreams.set(type, dummyStream);
                await rtcSession.updateStreamState(type, true);

                // Trigger bus event to notify CallParticipantVideo to attach track
                this.store.env.bus.trigger("LIVEKIT:TRACK:REBIND", {
                    sessionId: rtcSession.id,
                    type: type,
                });
            }
        });
        if (this.state.channel) {
            await this.call();
            await this.updateUpload();
        }
    },

    async updateUpload() {
        console.log("Updating uploads for tracks...");
        await this.network?.updateUpload(Source.MICROPHONE, this.state.audioTrack);
        await this.network?.updateUpload(Source.CAMERA, this.state.cameraTrack);
        await this.network?.updateUpload(Source.SCREEN, this.state.screenTrack);

        // Trigger rebind for local tracks after upload
        if (this.selfSession) {
            this.store.env.bus.trigger("LIVEKIT:TRACK:REBIND", {
                sessionId: this.selfSession.id,
                type: "local",
            });
        }
    },

    async call() {
        if (this.network.isConnected()) {
            return;
        }
        try {
            console.log("Connecting to LiveKit server...");
            await this.network.connect(
                this.selfSession.livekit_url,
                this.selfSession.livekit_token
            );
            this.selfSession.connectionState = "connected";
        } catch (error) {
            console.error("Failed to connect to LiveKit server:", error);
            this.selfSession.connectionState = "failed";
        }
    },

    async _loadSfu() {
        // No-op
    },

    _handleSfuClientStateChange() {
        // No-op
    },

    async _upgradeConnection() {
        // No-op
    },

    async _downgradeConnection() {
        // No-op
    },

    async leaveCall(...args) {
        this.network?.disconnect();
        return super.leaveCall(...args);
    },

    updateActiveSession(session, videoType, {addVideo = false} = {}) {
        this.state.channel ??= session.channel;
        return super.updateActiveSession(session, videoType, {addVideo});
    },

    clear() {
        this.network?.disconnect();
        return super.clear();
    },
});

patch(rtcService, {
    dependencies: [
        "bus_service",
        "discuss.p2p",
        "discuss.ptt_extension",
        "mail.sound_effects",
        "mail.store",
        "notification",
    ],
    start(env, services) {
        const store = env.services["mail.store"];
        const rtc = store.rtc;

        rtc.bus = services.bus_service;
        rtc.p2pService = services["discuss.p2p"];
        rtc.p2pService.acceptOffer = async () => {
            // Always reject P2P offers when LiveKit is enabled
            return false;
        };
        services.bus_service.subscribe(
            "discuss.channel.rtc.session/sfu_hot_swap",
            async () => {
                // Ignore SFU hot-swap for LiveKit
            }
        );
        services.bus_service.subscribe(
            "discuss.channel.rtc.session/ended",
            ({sessionId}) => {
                if (rtc.selfSession?.id === sessionId) {
                    rtc.endCall();
                    services.notification.add(
                        _t("Disconnected from the RTC call by the server"),
                        {
                            type: "warning",
                        }
                    );
                }
            }
        );
        services.bus_service.subscribe("res.users.settings.volumes", (payload) => {
            if (payload) {
                rtc.store.Volume.insert(payload);
            }
        });
        services.bus_service.subscribe(
            "discuss.channel.rtc.session/update_and_broadcast",
            (payload) => {
                const {data} = payload;
                // Apply updates even for active channel since LiveKit does not use P2P for real-time
                rtc.store.insert(data);
            }
        );
        return rtc;
    },
});
