/** @odoo-module */

console.debug("livekit bundle included");

import {
    HOST_TAKEOVER_DELAY_MS,
    LIVEKIT_HOST_MSG,
    parseLivekitIdentity,
} from "./livekit_utils";
import {LivekitCameraManager} from "./livekit_camera_manager";
import {LivekitCrossTabCoordinator} from "./livekit_cross_tab_coordinator";
import {LivekitMicrophoneManager} from "./livekit_microphone_manager";
import {LivekitRoomManager} from "./livekit_room_manager";
import {LivekitScreenShareManager} from "./livekit_screen_share_manager";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {onChange} from "@mail/utils/common/misc";
import {reactive} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";
import {url} from "@web/core/utils/urls";

export const livekitService = {
    dependencies: ["notification", "mail.store"],
    start(env) {
        const debugEnabled = (() => {
            try {
                const search = window?.location?.search || "";
                return new URLSearchParams(search).has("debug");
            } catch {
                return false;
            }
        })();

        const log = debugEnabled ? console.log.bind(console) : () => undefined;
        const warn = debugEnabled ? console.warn.bind(console) : () => undefined;

        const state = reactive({
            channel: null,
            room: null,
            connecting: false,
            connected: false,
            micEnabled: true,
            cameraEnabled: false,
            screenShareEnabled: false,
            deafened: false,
            videoTracks: [],
            isHost: false,
            hostedChannelId: null,
            hostedSessionId: null,
        });

        const store = env.services["mail.store"];

        let pageHideCleanup = null;
        /** @type {Map<string, HTMLMediaElement>} */
        const attachedAudioEls = new Map();

        let disconnectCleanupInProgress = false;
        let manualDisconnectInProgress = false;

        function _sendJsonRpcBeacon(route, params) {
            try {
                const endpoint = url(route);
                const body = JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params,
                    id: Date.now(),
                });
                const blob = new Blob([body], {type: "application/json"});
                if (navigator?.sendBeacon) {
                    navigator.sendBeacon(endpoint, blob);
                    return;
                }
                // Fallback: best-effort keepalive fetch.
                fetch(endpoint, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    credentials: "include",
                    keepalive: true,
                    body,
                });
            } catch (e) {
                warn("Beacon send failed:", e);
            }
        }

        function isScreenShareSource(source) {
            // LiveKit source values can be enums or strings depending on build.
            return (
                source === "screen_share" ||
                source === "screenshare" ||
                source === "screen" ||
                source === "ScreenShare" ||
                source === "SCREEN_SHARE"
            );
        }

        function publicationToType(publication) {
            const src = publication?.source;
            return isScreenShareSource(src) ? "screen" : "camera";
        }

        function clearTracks() {
            state.videoTracks.splice(0, state.videoTracks.length);
        }

        function upsertVideoTrack(id, participantName, track) {
            const existingIndex = state.videoTracks.findIndex((t) => t.id === id);
            const item = {id, participantName, track};
            if (existingIndex >= 0) {
                state.videoTracks.splice(existingIndex, 1, item);
            } else {
                state.videoTracks.push(item);
            }
        }

        function removeVideoTrack(id) {
            const index = state.videoTracks.findIndex((t) => t.id === id);
            if (index >= 0) {
                state.videoTracks.splice(index, 1);
            }
        }

        function getRtcSessionForLivekitIdentity(channel, identity) {
            const {partnerId, guestId} = parseLivekitIdentity(identity);
            if (!partnerId && !guestId) {
                return undefined;
            }
            const sessions = channel?.rtcSessions ? [...channel.rtcSessions] : [];
            return sessions.find(
                (s) =>
                    (partnerId && s.partnerId === partnerId) ||
                    (guestId && s.guestId === guestId)
            );
        }

        function updateTalkingFromRoom(room, channel) {
            try {
                const adapter = env.services["discuss.livekit_rtc_adapter"];
                const channelId = channel?.id;
                const active = room?.activeSpeakers || [];
                const identities = active.map((p) => p?.identity).filter(Boolean);

                adapter?.updateTalkingStates?.(channelId, identities);
            } catch (e) {
                warn("updateTalkingFromRoom error:", e);
            }
        }

        function setSelfConnectionState(channel, connectionState) {
            try {
                const rtc = env.services["discuss.rtc"];
                // Only reflect state when the synthetic call UI is active for this channel.
                if (rtc?.selfSession && rtc?.state?.channel?.id === channel?.id) {
                    rtc.selfSession.connectionState = connectionState;
                }
            } catch (e) {
                warn("setSelfConnectionState error:", e);
            }
        }

        function createConnectionStateHandler(channel) {
            // Avoid spamming toasts during LiveKit reconnect loops.
            let lastLivekitConnectionState = "";
            let reconnectToastShown = false;

            return (nextState) => {
                // LiveKit passes a string enum: "connected" | "reconnecting" | "disconnected".
                const stateStr = String(nextState || "");
                if (stateStr === lastLivekitConnectionState) {
                    return;
                }
                lastLivekitConnectionState = stateStr;

                if (stateStr === "reconnecting") {
                    setSelfConnectionState(channel, "reconnecting");
                    if (!reconnectToastShown) {
                        reconnectToastShown = true;
                        try {
                            env.services.notification.add(
                                _t("Connection lost. Reconnecting..."),
                                {
                                    type: "warning",
                                    sticky: true,
                                }
                            );
                        } catch (e) {
                            warn("Failed to show reconnecting notification:", e);
                        }
                    }
                    return;
                }

                if (stateStr === "connected") {
                    setSelfConnectionState(channel, "connected");
                    if (reconnectToastShown) {
                        reconnectToastShown = false;
                        try {
                            env.services.notification.add(_t("Connection restored."), {
                                type: "success",
                            });
                        } catch (e) {
                            warn("Failed to show connection restored notification:", e);
                        }
                    }
                    return;
                }

                if (stateStr === "disconnected") {
                    setSelfConnectionState(channel, "disconnected");
                }
            };
        }

        const cameraManager = new LivekitCameraManager(env, state, warn, log);

        const microphoneManager = new LivekitMicrophoneManager(env, state, warn, log);

        const screenShareManager = new LivekitScreenShareManager(
            env,
            state,
            warn,
            publicationToType
        );

        const crossTabCoordinator = new LivekitCrossTabCoordinator(state, warn);

        /** @type {LivekitRoomManager|null} */
        let roomManager = null;

        // Keep microphone input device selection in sync while in a call.
        try {
            if (store?.settings) {
                onChange(store.settings, "audioInputDeviceId", async () => {
                    // Only the host tab publishes audio.
                    if (!state.connected || !state.isHost || !state.micEnabled) {
                        return;
                    }
                    try {
                        await microphoneManager.restartMicrophoneWithSelectedDevice();
                    } catch (e) {
                        warn("Failed to switch microphone device", e);
                        env.services.notification.add(
                            `Microphone failed: ${e?.message || e}`,
                            {
                                type: "warning",
                            }
                        );
                        // Fall back to muted if switching fails.
                        await microphoneManager.setMicrophoneEnabled(false);
                        const presence = env.services["discuss.livekit_presence"];
                        if (state.channel && state.isHost) {
                            await presence?.updatePresence(state.channel, {
                                is_muted: true,
                            });
                        }
                    }
                });
            }
        } catch (e) {
            // Some environments may not provide onChange; ignore.
            warn("Failed to setup audioInputDeviceId watcher", e);
        }

        async function leave() {
            const channel = state.channel;
            const wasHost = state.isHost;
            const wasChannelId = state.hostedChannelId;

            manualDisconnectInProgress = true;
            try {
                log("leave()", {
                    wasConnected: state.connected,
                    channelId: channel?.id,
                    wasHost,
                });

                // Clear cross-tab state early to prevent race conditions
                state.isHost = false;
                state.hostedChannelId = null;
                state.hostedSessionId = null;

                // If we were host, broadcast close to remotes
                if (wasHost && wasChannelId) {
                    crossTabCoordinator.postBroadcast({
                        type: LIVEKIT_HOST_MSG.CLOSE,
                        channelId: wasChannelId,
                        reason: "disconnect",
                    });
                    crossTabCoordinator.stopHostPing();
                }

                state.connecting = false;
                try {
                    state.room?.disconnect?.();
                } catch (error) {
                    warn("room disconnect failed", error);
                }
            } finally {
                try {
                    await cameraManager.cleanup();
                } catch (error) {
                    warn("local camera cleanup failed", error);
                }

                try {
                    await microphoneManager.cleanup();
                } catch (error) {
                    warn("local microphone cleanup failed", error);
                }

                // Clear talking indicators for this channel.
                try {
                    env.services["discuss.livekit_rtc_adapter"]?.updateTalkingStates?.(
                        channel?.id,
                        []
                    );
                } catch (e) {
                    warn("Failed to clear talking states:", e);
                }

                // Reset local state even if server RPCs fail (offline/transient errors).
                state.room = null;
                state.channel = null;
                state.connected = false;
                state.deafened = false;
                state.cameraEnabled = false;

                try {
                    clearTracks();
                } catch (e) {
                    warn("Failed to clear tracks:", e);
                }
                try {
                    if (roomManager) {
                        roomManager.clearRemoteAudio();
                    }
                } catch (e) {
                    warn("Failed to clear remote audio:", e);
                }

                const presence = env.services["discuss.livekit_presence"];
                if (channel) {
                    try {
                        await presence?.leavePresence(channel);
                    } catch (error) {
                        warn("presence leave failed", error);
                    }
                }

                if (pageHideCleanup) {
                    try {
                        browser.removeEventListener("pagehide", pageHideCleanup);
                    } catch (e) {
                        warn("Failed to remove pagehide listener:", e);
                    }
                }
                pageHideCleanup = null;
                manualDisconnectInProgress = false;
            }
        }

        roomManager = new LivekitRoomManager({
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
            getManualDisconnectInProgress: () => manualDisconnectInProgress,
            getDisconnectCleanupInProgress: () => disconnectCleanupInProgress,
            setDisconnectCleanupInProgress: (value) => {
                disconnectCleanupInProgress = Boolean(value);
            },
            leave,
        });

        // Subscribe to cross-tab coordination events
        crossTabCoordinator.on("hostConflict", () => {
            const channelToClose = state.channel;
            try {
                const rtc = env.services["discuss.rtc"];
                if (rtc && channelToClose) {
                    rtc.leaveCall(channelToClose).catch((err) => {
                        warn("Forced disconnect during host conflict:", err);
                    });
                } else {
                    leave().catch((err) => {
                        warn("Leave failed during host conflict:", err);
                    });
                }
            } catch (e) {
                warn("Exception during host conflict handling:", e);
                leave().catch((err) => {
                    warn("Leave failed in exception handler:", err);
                });
            }
        });

        crossTabCoordinator.on("hostTakeover", () => {
            const channelToClose = state.channel;
            try {
                const rtc = env.services["discuss.rtc"];
                if (rtc && channelToClose) {
                    rtc.leaveCall(channelToClose).catch((err) => {
                        warn("Forced disconnect during host close:", err);
                    });
                } else {
                    leave().catch((err) => {
                        warn("Leave failed during host close:", err);
                    });
                }
            } catch (e) {
                warn("Exception during host close handling:", e);
                leave().catch((err) => {
                    warn("Leave failed in exception handler:", err);
                });
            }
        });

        async function setMicEnabled(enabled) {
            if (!state.room) {
                return;
            }
            try {
                await microphoneManager.setMicrophoneEnabled(Boolean(enabled));
            } catch (e) {
                warn("setMicEnabled() failed", e);
                env.services.notification.add(`Microphone failed: ${e?.message || e}`, {
                    type: "warning",
                });
                try {
                    await microphoneManager.setMicrophoneEnabled(false);
                } catch {
                    // Ignore
                }
            }
            const presence = env.services["discuss.livekit_presence"];
            // Only host should update presence
            if (state.channel && state.isHost) {
                await presence?.updatePresence(state.channel, {
                    is_muted: !state.micEnabled,
                });
            }
        }

        function _getPresenceService() {
            return env.services["discuss.livekit_presence"];
        }

        async function _disconnectIfConnected() {
            if (!state.connected) {
                return;
            }
            log("Already connected; leaving first", {channelId: state.channel?.id});
            await leave();
        }

        async function _takeOverIfHostActive(channel) {
            const hostActive = await crossTabCoordinator.probeForActiveHost(channel.id);
            if (!hostActive) {
                return;
            }

            log("Active host detected in another tab; taking over as new host", {
                channelId: channel.id,
            });

            crossTabCoordinator.postBroadcast({
                type: LIVEKIT_HOST_MSG.CLOSE,
                channelId: channel.id,
                reason: "takeover",
            });

            await new Promise((resolve) => setTimeout(resolve, HOST_TAKEOVER_DELAY_MS));
        }

        async function _createAndConnectRoom(channel, payload) {
            const LivekitClient = window.LivekitClient;

            const room = new LivekitClient.Room();
            clearTracks();

            roomManager.setupRoomEventHandlers(room, channel, LivekitClient);

            log("room.connect()", {url: payload?.livekit_url});
            await room.connect(payload.livekit_url, payload.token);

            try {
                await room.startAudio();
            } catch {
                warn("room.startAudio() failed (autoplay policy?)");
            }

            return room;
        }

        function _markConnectedAndClaimHost(room, channel, presence) {
            state.room = room;
            state.connected = true;
            updateTalkingFromRoom(room, channel);

            state.isHost = true;
            state.hostedChannelId = channel.id;
            state.hostedSessionId = presence?.state?.selfSessionIdByChannelId?.get(
                channel.id
            );

            crossTabCoordinator.sendHostSnapshot();
            crossTabCoordinator.startHostPing();
        }

        async function _initMicAndPresenceAfterJoin(channel, presence, audio) {
            try {
                await microphoneManager.setMicrophoneEnabled(Boolean(audio));
            } catch (e) {
                warn("microphone init failed; joining muted", e);
                env.services.notification.add(`Microphone failed: ${e?.message || e}`, {
                    type: "warning",
                });
                try {
                    await microphoneManager.setMicrophoneEnabled(false);
                } catch {
                    // Ignore
                }
            }

            state.cameraEnabled = false;

            await presence?.updatePresence(channel, {
                is_muted: !state.micEnabled,
                is_camera_on: state.cameraEnabled,
            });
        }

        async function _enableCameraIfRequested(camera) {
            if (!camera) {
                return;
            }
            await cameraManager.setCameraEnabled(true);
        }

        function _ensurePageHideBeacon() {
            pageHideCleanup =
                pageHideCleanup ||
                (() => {
                    try {
                        const channelId = state.channel?.id;
                        if (!channelId) {
                            return;
                        }
                        _sendJsonRpcBeacon("/mail/livekit/channel/leave_call", {
                            channel_id: channelId,
                        });
                    } catch {
                        // Ignore
                    }
                });
            browser.addEventListener("pagehide", pageHideCleanup);
        }

        async function join(channel, {audio = true, camera = false} = {}) {
            state.connecting = true;
            try {
                await _disconnectIfConnected();

                // Set early so media events can always map to a channel.
                state.channel = channel;

                await _takeOverIfHostActive(channel);

                const presence = _getPresenceService();
                await presence?.joinPresence(channel, {audio, camera});

                const payload = await rpc("/livekit/token", {channel_id: channel.id});
                const room = await _createAndConnectRoom(channel, payload);

                _markConnectedAndClaimHost(room, channel, presence);

                await _initMicAndPresenceAfterJoin(channel, presence, audio);
                await _enableCameraIfRequested(camera);

                _ensurePageHideBeacon();
                return true;
            } catch (error) {
                warn("join() failed", error);
                env.services.notification.add(
                    `LiveKit call failed: ${error?.message || error}`,
                    {type: "danger"}
                );
                await leave();
                return false;
            } finally {
                state.connecting = false;
            }
        }

        async function setScreenShareEnabled(enabled) {
            await screenShareManager.setScreenShareEnabled(enabled);
        }
        async function setDeaf(enabled) {
            state.deafened = Boolean(enabled);
            for (const el of attachedAudioEls.values()) {
                try {
                    el.muted = state.deafened;
                } catch {
                    // Ignore
                }
            }
            const presence = env.services["discuss.livekit_presence"];
            // Only host should update presence
            if (state.channel && state.isHost) {
                await presence?.updatePresence(state.channel, {
                    is_deaf: state.deafened,
                });
            }
        }

        async function toggleMic() {
            if (!state.room) {
                return;
            }
            await setMicEnabled(!state.micEnabled);
        }

        async function toggleCamera() {
            if (!state.room) {
                return;
            }
            await cameraManager.toggleCamera();
        }

        function isInCall(channel) {
            return Boolean(
                state.connected && state.channel && state.channel.eq(channel)
            );
        }

        // Initialize cross-tab coordination
        crossTabCoordinator.initBroadcastChannel();

        return {
            state,
            join,
            leave,
            toggleMic,
            toggleCamera,
            setScreenShareEnabled,
            setMicEnabled,
            setCameraEnabled: (enabled) => cameraManager.setCameraEnabled(enabled),
            setDeaf,
            isInCall,
        };
    },
};

registry.category("services").add("discuss.livekit", livekitService);
