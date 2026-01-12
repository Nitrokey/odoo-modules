/** @odoo-module */

import {_t} from "@web/core/l10n/translation";

/**
 * Room manager for LiveKit rooms.
 * Owns room event wiring and remote audio element lifecycle.
 */
export class LivekitRoomManager {
    /**
     * @param {Object} options
     * @param {Object} options.env
     * @param {Object} options.state
     * @param {Function} options.log
     * @param {Function} options.warn
     * @param {Object} options.store
     * @param {Map<String, HTMLMediaElement>} options.attachedAudioEls
     * @param {Function} options.getRtcSessionForLivekitIdentity
     * @param {Function} options.publicationToType
     * @param {Function} options.upsertVideoTrack
     * @param {Function} options.removeVideoTrack
     * @param {Function} options.updateTalkingFromRoom
     * @param {Function} options.setSelfConnectionState
     * @param {Function} options.createConnectionStateHandler
     * @param {Function} options.getManualDisconnectInProgress
     * @param {Function} options.getDisconnectCleanupInProgress
     * @param {Function} options.setDisconnectCleanupInProgress
     * @param {Function} options.leave
     */
    constructor({
        env,
        state,
        log,
        warn,
        store,
        attachedAudioEls,
        getRtcSessionForLivekitIdentity,
        publicationToType,
        upsertVideoTrack,
        removeVideoTrack,
        updateTalkingFromRoom,
        setSelfConnectionState,
        createConnectionStateHandler,
        getManualDisconnectInProgress,
        getDisconnectCleanupInProgress,
        setDisconnectCleanupInProgress,
        leave,
    }) {
        this.env = env;
        this.state = state;
        this.log = log;
        this.warn = warn;
        this.store = store;
        this.attachedAudioEls = attachedAudioEls;
        this.getRtcSessionForLivekitIdentity = getRtcSessionForLivekitIdentity;
        this.publicationToType = publicationToType;
        this.upsertVideoTrack = upsertVideoTrack;
        this.removeVideoTrack = removeVideoTrack;
        this.updateTalkingFromRoom = updateTalkingFromRoom;
        this.setSelfConnectionState = setSelfConnectionState;
        this.createConnectionStateHandler = createConnectionStateHandler;
        this.getManualDisconnectInProgress = getManualDisconnectInProgress;
        this.getDisconnectCleanupInProgress = getDisconnectCleanupInProgress;
        this.setDisconnectCleanupInProgress = setDisconnectCleanupInProgress;
        this.leave = leave;
    }

    attachRemoteAudio(id, track, {channel, identity} = {}) {
        // `track.attach()` returns an HTMLMediaElement (typically <audio>).
        const el = track.attach();
        if (!(el instanceof HTMLMediaElement)) {
            return;
        }
        el.autoplay = true;
        el.muted = Boolean(this.state.deafened);
        el.playsInline = true;
        el.style.display = "none";

        // Per-participant volume parity: bind this element to the related RtcSession.
        try {
            const session = this.getRtcSessionForLivekitIdentity(channel, identity);
            if (session) {
                try {
                    el.volume = this.store.settings.getVolume(session);
                } catch {
                    // Ignore
                }
                session.audioElement = el;
                if (el.srcObject instanceof MediaStream) {
                    session.audioStream = el.srcObject;
                }
            }
        } catch {
            // Ignore
        }

        // Avoid duplicates.
        const existing = this.attachedAudioEls.get(id);
        if (existing && existing !== el) {
            try {
                existing.remove();
            } catch {
                // Ignore
            }
        }
        this.attachedAudioEls.set(id, el);
        document.body.appendChild(el);
    }

    detachRemoteAudio(id, track, {channel, identity} = {}) {
        const el = this.attachedAudioEls.get(id);
        if (el) {
            this.attachedAudioEls.delete(id);
            try {
                el.remove();
            } catch {
                // Ignore
            }

            try {
                const session = this.getRtcSessionForLivekitIdentity(channel, identity);
                if (session?.audioElement === el) {
                    session.audioElement = undefined;
                    session.audioStream = undefined;
                }
            } catch {
                // Ignore
            }
        }
        try {
            track.detach();
        } catch {
            // Ignore
        }
    }

    clearRemoteAudio() {
        for (const el of this.attachedAudioEls.values()) {
            try {
                el.remove();
            } catch {
                // Ignore
            }
        }
        this.attachedAudioEls.clear();
    }

    setupRoomEventHandlers(room, channel, LivekitClient) {
        const onConnectionState = this.createConnectionStateHandler(channel);

        room.on(LivekitClient.RoomEvent.Connected, () => {
            this.log("RoomEvent.Connected", {
                room: room.name,
                identity: room.localParticipant?.identity,
            });
            this.setSelfConnectionState(channel, "connected");
        });

        room.on(LivekitClient.RoomEvent.ParticipantConnected, (participant) => {
            this.log("RoomEvent.ParticipantConnected", {
                identity: participant?.identity,
                name: participant?.name,
            });
            this.updateTalkingFromRoom(room, channel);
        });

        room.on(LivekitClient.RoomEvent.ParticipantDisconnected, (participant) => {
            this.log("RoomEvent.ParticipantDisconnected", {
                identity: participant?.identity,
                name: participant?.name,
            });
            this.updateTalkingFromRoom(room, channel);
        });

        // LiveKit speaking detection: update active speakers to drive the native UI.
        // Event name differs by SDK version, so guard on existence.
        const activeSpeakersEvent = LivekitClient.RoomEvent?.ActiveSpeakersChanged;
        if (activeSpeakersEvent) {
            room.on(activeSpeakersEvent, () => this.updateTalkingFromRoom(room, channel));
        }

        // Parity with base RTC: show a warning badge when connection is unstable.
        if (LivekitClient.RoomEvent?.Reconnecting) {
            room.on(LivekitClient.RoomEvent.Reconnecting, () => {
                this.log("RoomEvent.Reconnecting");
                onConnectionState("reconnecting");
            });
        }
        if (LivekitClient.RoomEvent?.Reconnected) {
            room.on(LivekitClient.RoomEvent.Reconnected, () => {
                this.log("RoomEvent.Reconnected");
                onConnectionState("connected");
            });
        }

        // Some SDK versions primarily emit ConnectionStateChanged during reconnects.
        const connectionStateChangedEvent = LivekitClient.RoomEvent?.ConnectionStateChanged;
        if (connectionStateChangedEvent) {
            room.on(connectionStateChangedEvent, (s) => {
                this.log("RoomEvent.ConnectionStateChanged", {state: s});
                onConnectionState(s);
            });
        }

        room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            const key = `remote_${participant.identity}_${publication.trackSid}`;
            this.log("RoomEvent.TrackSubscribed", {
                key,
                kind: track?.kind,
                participant: participant?.identity,
                trackSid: publication?.trackSid,
            });
            if (track.kind === "video") {
                this.upsertVideoTrack(key, participant.name || participant.identity, track);
                try {
                    const adapter = this.env.services["discuss.livekit_rtc_adapter"];
                    const mediaStreamTrack = track?.mediaStreamTrack;
                    const type = this.publicationToType(publication);
                    if (adapter && channel?.id) {
                        adapter.setLivekitVideoTrackForIdentity(channel.id, participant.identity, {
                            type,
                            track,
                        });
                        if (mediaStreamTrack) {
                            adapter.setStreamForIdentity(channel.id, participant.identity, {
                                type,
                                mediaStreamTrack,
                            });
                        }
                    }
                } catch (e) {
                    this.warn("Failed to set video track in adapter:", e);
                }
            } else if (track.kind === "audio") {
                this.attachRemoteAudio(key, track, {channel, identity: participant.identity});
            }
        });

        room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
            const key = `remote_${participant.identity}_${publication.trackSid}`;
            this.log("RoomEvent.TrackUnsubscribed", {
                key,
                kind: track?.kind,
                participant: participant?.identity,
                trackSid: publication?.trackSid,
            });
            if (track.kind === "video") {
                this.removeVideoTrack(key);
                try {
                    const adapter = this.env.services["discuss.livekit_rtc_adapter"];
                    const type = this.publicationToType(publication);
                    if (adapter && channel?.id) {
                        adapter.removeLivekitVideoTrackForIdentity(channel.id, participant.identity, {
                            type,
                        });
                        adapter.removeStreamForIdentity(channel.id, participant.identity, {
                            type,
                        });
                    }
                } catch (e) {
                    this.warn("Failed to remove video track from adapter:", e);
                }
            } else if (track.kind === "audio") {
                this.detachRemoteAudio(key, track, {channel, identity: participant.identity});
            }
        });

        room.on(LivekitClient.RoomEvent.Disconnected, () => {
            this.log("RoomEvent.Disconnected");
            this.updateTalkingFromRoom(room, channel);
            if (this.getManualDisconnectInProgress()) {
                return;
            }

            // Immediately reflect the transport failure in the native UI.
            this.setSelfConnectionState(channel, "disconnected");

            // If LiveKit disconnects unexpectedly, clean up the native call UI.
            if (this.getDisconnectCleanupInProgress()) {
                return;
            }
            this.setDisconnectCleanupInProgress(true);

            try {
                this.env.services.notification.add(_t("Disconnected from the RTC call by the server"), {
                    type: "warning",
                });
            } catch (e) {
                this.warn("Failed to show disconnection notification:", e);
            }

            const channelToClose = this.state.channel;
            const rtc = this.env.services["discuss.rtc"];
            const closePromise = channelToClose && rtc?.leaveCall ? rtc.leaveCall(channelToClose) : this.leave();
            Promise.resolve(closePromise).finally(() => {
                this.setDisconnectCleanupInProgress(false);
            });
        });
    }
}
