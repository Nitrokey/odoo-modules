// @odoo-module
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
        console.debug("message intercepted");
    },

    _dataChannelupdateInBroadcast() {
        console.debug("message intercepted");
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

    identityToSessionId(identity) {
        // Convert LiveKit identity back to session ID
        if (identity.startsWith("partner:")) {
            const partnerId = parseInt(identity.split(":")[1], 10);
            // Find the session with this partner ID
            for (const session of this.state.channel.rtcSessions) {
                if (session.partnerId === partnerId) {
                    return session.id;
                }
            }
        } else if (identity.startsWith("guest:")) {
            const guestId = parseInt(identity.split(":")[1], 10);
            // Find the session with this channel member ID
            for (const session of this.state.channel.rtcSessions) {
                if (session.channelMember.id === guestId) {
                    return session.id;
                }
            }
        }
        return identity;
    },

    fixEventIds(eventdata) {
        if (eventdata.detail.payload.identity && !eventdata.detail.payload.sessionId) {
            eventdata.detail.payload.sessionId = this.identityToSessionId(
                eventdata.detail.payload.identity
            );
        }
        if (
            eventdata.detail.name === "info_change" &&
            Object.keys(eventdata.detail.payload)[0].includes(":")
        ) {
            const fixedIdentity = this.identityToSessionId(
                Object.keys(eventdata.detail.payload)[0]
            );
            eventdata.detail.payload = {
                [fixedIdentity]:
                    eventdata.detail.payload[Object.keys(eventdata.detail.payload)[0]],
            };
        }
    },

    async _handleNetworkUpdates(eventdata) {
        console.debug("LIVEKIT: Network update received", eventdata);
        this.fixEventIds(eventdata);
        const result = await super._handleNetworkUpdates(eventdata);
        // When a remote video stream stops (screen share ends, camera turned
        // off, ...) or a participant's info changes, the focused (active)
        // session may no longer have anything to display. In that case, leave
        // the focus view and fall back to the tile view instead of showing an
        // empty screen.
        const name = eventdata.detail?.name;
        if (
            (name === "track" && eventdata.detail?.payload?.active === false) ||
            name === "info_change"
        ) {
            this._exitFocusModeIfNeeded();
        }
        return result;
    },

    _exitFocusModeIfNeeded() {
        const channel = this.state.channel;
        const focused = channel?.activeRtcSession;
        if (!focused) {
            return;
        }
        // The main (focused) video stream is still active, nothing to do.
        if (focused.isMainVideoStreamActive) {
            return;
        }
        if (focused.isCameraOn) {
            // Fall back to the camera stream if it is still available.
            focused.mainVideoStreamType = "camera";
        } else if (focused.isScreenSharingOn) {
            // Fall back to the screen share stream if it is still available.
            focused.mainVideoStreamType = "screen";
        } else {
            // Nothing left to display for this session: exit the focus view
            // and return to the tile view.
            channel.activeRtcSession = undefined;
            focused.mainVideoStreamType = undefined;
        }
    },

    async setAudioVolume(sessionId, element = null) {
        const rtcSession = await this.store.RtcSession.getWhenReady(sessionId);
        if (element) {
            rtcSession.audioElement = element;
        }
        const volumeSetting = this.store.Volume.getForPartnerId(rtcSession.partnerId);
        const volume = volumeSetting ? volumeSetting.volume / 100 : 1.0;
        if (rtcSession.audioElement) {
            rtcSession.audioElement.volume = volume;
        }
    },

    async handleSetAudioVolume(eventdata) {
        console.debug("LIVEKIT: Set audio volume event received", eventdata);
        this.fixEventIds(eventdata);
        return this.setAudioVolume(
            eventdata.detail.payload.sessionId,
            eventdata.detail.payload.element
        );
    },

    async handleTrackSubscribed(eventdata) {
        console.debug("LIVEKIT: Track subscribed event received", eventdata);
        this.fixEventIds(eventdata);
        if (eventdata.detail.name === "trackSubscribed") {
            const {identity, type, track} = eventdata.detail.payload;
            const sessionId = this.identityToSessionId(identity);

            console.debug(
                `Track subscribed for session ${sessionId}, type ${type}. Triggering rebind.`
            );

            const rtcSession = await this.store.RtcSession.getWhenReady(sessionId);

            // Store LiveKit track separately
            rtcSession.livekitTracks.set(type, track);

            // Create dummy MediaStream for UI rendering (hasVideo check)
            const dummyStream = new window.MediaStream();
            rtcSession.videoStreams.set(type, dummyStream);
            await rtcSession.updateStreamState(type, true);

            // When a remote participant starts sharing their screen, switch
            // every other attendee to the focus (single-tile) view showing that
            // screen share.
            const channel = this.state.channel;
            if (
                type === "screen" &&
                channel &&
                rtcSession.notEq(this.selfSession)
            ) {
                rtcSession.mainVideoStreamType = "screen";
                channel.activeRtcSession = rtcSession;
            }

            // Trigger bus event to notify CallParticipantVideo to attach track
            this.store.env.bus.trigger("LIVEKIT:TRACK:REBIND", {
                sessionId: rtcSession.id,
                type: type,
                identity: identity,
            });
        }
    },

    async _initConnection() {
        this.selfSession.connectionState = "selecting network type";
        await this.network?.disconnect();
        this.network = new LiveKitAdapter();
        this.state.connectionType = CONNECTION_TYPES.SERVER;

        this.network.addEventListener("update", this._handleNetworkUpdates.bind(this));
        this.network.addEventListener(
            "updateTrack",
            this.handleTrackSubscribed.bind(this)
        );

        if (this.state.channel) {
            await this.call();
            await this.updateUpload();
        }
    },

    async updateUpload() {
        console.debug("Updating uploads for tracks...");
        await this.network?.updateUpload(Source.MICROPHONE, this.state.audioTrack);
        await this.network?.updateUpload(
            Source.CAMERA,
            this.state.sendCamera ? this.state.cameraTrack : null
        );
        await this.network?.updateUpload(
            Source.SCREEN,
            this.state.sendScreen ? this.state.screenTrack : null
        );

        // Trigger rebind for local tracks after upload
        if (this.selfSession) {
            this.store.env.bus.trigger("LIVEKIT:TRACK:REBIND", {
                sessionId: this.selfSession.id,
                type: "local",
            });
        }
    },

    async call() {
        if (!this.network || this.network.isConnected()) {
            return;
        }
        try {
            console.debug("Connecting to LiveKit server...");
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

    _clearRemoteLiveKitTracks(channel) {
        for (const session of channel.rtcSessions) {
            if (session.livekitTracks) {
                // Detach all tracks before clearing
                for (const track of session.livekitTracks.values()) {
                    track?.detach?.();
                }
                session.livekitTracks.clear();
            }
        }
    },

    _clearLocalLiveKitTracks() {
        if (this.selfSession?.livekitTracks) {
            // Detach all tracks before clearing
            for (const track of this.selfSession.livekitTracks.values()) {
                track?.detach?.();
            }
            this.selfSession.livekitTracks.clear();
        }
    },

    clear() {
        this.network?.disconnect();
        if (this.state.channel) {
            this._clearRemoteLiveKitTracks(this.state.channel);
        }
        this._clearLocalLiveKitTracks();
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
