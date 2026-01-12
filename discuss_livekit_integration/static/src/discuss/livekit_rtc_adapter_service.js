/** @odoo-module */

import {CONNECTION_TYPES} from "@mail/discuss/call/common/rtc_service";
import {_t} from "@web/core/l10n/translation";
import {parseLivekitIdentity} from "./livekit/livekit_utils";
import {registry} from "@web/core/registry";

function parseOdooDatetime(value) {
    if (!value) {
        return undefined;
    }
    if (value instanceof Date) {
        return value;
    }
    if (typeof value === "string") {
        // Odoo typically serializes datetimes as "YYYY-MM-DD HH:MM:SS".
        // Convert to a strict ISO string for reliable parsing.
        if (value.includes("T")) {
            const d = new Date(value);
            return Number.isNaN(d.getTime()) ? undefined : d;
        }
        if (value.includes(" ")) {
            const d = new Date(value.replace(" ", "T") + "Z");
            return Number.isNaN(d.getTime()) ? undefined : d;
        }
        const d = new Date(value);
        return Number.isNaN(d.getTime()) ? undefined : d;
    }
    return undefined;
}

export const livekitRtcAdapterService = {
    dependencies: ["mail.store", "bus_service", "discuss.livekit_presence"],
    async start(env, services) {
        const store = services["mail.store"];
        const bus = services.bus_service;
        const presence = services["discuss.livekit_presence"];

        const debugEnabled = (() => {
            try {
                const search = window?.location?.search || "";
                return new URLSearchParams(search).has("debug");
            } catch {
                return false;
            }
        })();
        const warn = debugEnabled ? console.warn.bind(console) : () => undefined;

        // Use negative IDs to avoid any collision with real RTC sessions.
        const toRtcSessionId = (livekitSessionId) => -Number(livekitSessionId);

        /** @type {Map<string, any>} key -> LiveKit VideoTrack */
        const livekitVideoTracks = new Map();

        const trackKey = (rtcSessionId, type) => `${rtcSessionId}:${type}`;

        function getThread(channelId) {
            return store.Thread.get({
                model: "discuss.channel",
                id: channelId,
            });
        }

        function getOrCreateChannelMember(presenceSession) {
            const channelMemberId = presenceSession.channelMemberId;
            if (!channelMemberId) {
                return undefined;
            }

            // Ensure the ChannelMember exists in the store. In some views the thread exists
            // but its members aren't loaded yet; we can create a minimal stub from the
            // LiveKit presence payload.
            let channelMember = store.ChannelMember?.get(channelMemberId);
            if (channelMember) {
                return channelMember;
            }

            const thread = getThread(presenceSession.channelId);
            if (!thread) {
                return undefined;
            }
            const personaType = presenceSession.partnerId ? "partner" : "guest";
            const personaId = Number(presenceSession.partnerId || presenceSession.guestId);
            if (!personaId) {
                return undefined;
            }

            try {
                store.Persona?.insert({
                    type: personaType,
                    id: personaId,
                    name: presenceSession.name || "",
                });
                store.ChannelMember?.insert({
                    id: channelMemberId,
                    thread: {
                        model: "discuss.channel",
                        id: presenceSession.channelId,
                    },
                    persona: {type: personaType, id: personaId},
                });
                channelMember = store.ChannelMember?.get(channelMemberId);
            } catch (e) {
                warn("Failed to create channel member:", e);
            }
            return channelMember;
        }

        function notifyRaiseHandTransition({presenceSession, rtcSessionId, wasRaisingHand, isRaisingHand}) {
            try {
                const rtc = env.services["discuss.rtc"];
                const selfId = presence?.state?.selfSessionIdByChannelId?.get(presenceSession.channelId);
                const isSelf = Boolean(selfId) && Number(presenceSession.id) === Number(selfId);
                if (!rtc || isSelf || wasRaisingHand === isRaisingHand) {
                    return;
                }
                const notificationId = "raise_hand_" + rtcSessionId;
                if (isRaisingHand) {
                    const session = store.RtcSession.get(rtcSessionId);
                    const name = session?.name || presenceSession.name || "";
                    rtc.addCallNotification({
                        id: notificationId,
                        text: _t("%s raised their hand", name),
                    });
                } else {
                    rtc.removeCallNotification(notificationId);
                }
            } catch (e) {
                warn("Failed to notify raise hand transition:", e);
            }
        }

        function ensureRtcSessionFromPresence(presenceSession) {
            const rtcSessionId = toRtcSessionId(presenceSession.id);
            const previousRtcSession = store.RtcSession.get(rtcSessionId);
            const wasRaisingHand = Boolean(previousRtcSession?.raisingHand);

            const channelMember = getOrCreateChannelMember(presenceSession);
            if (!channelMember) {
                return;
            }

            const raisingHand = parseOdooDatetime(presenceSession.raisingHand);

            const isRaisingHand = Boolean(raisingHand);

            // Synthetic sessions default to "connected" to avoid warning badges.
            // However, we must not overwrite an existing connectionState because
            // LiveKit may temporarily mark the local session as reconnecting/disconnected.
            const connectionState = previousRtcSession?.connectionState || "connected";

            store.RtcSession.insert({
                id: rtcSessionId,
                channelMember: presenceSession.channelMemberId,
                isCameraOn: Boolean(presenceSession.isCameraOn),
                isScreenSharingOn: Boolean(presenceSession.isScreenSharingOn),
                isSelfMuted: Boolean(presenceSession.isMuted),
                isDeaf: Boolean(presenceSession.isDeaf),
                raisingHand,
                connectionState,
            });

            // Base RTC behavior: notify when a remote participant raises/lowers their hand.
            // Also ensures the raised-hand ordering works (already handled by raisingHand Date).
            notifyRaiseHandTransition({presenceSession, rtcSessionId, wasRaisingHand, isRaisingHand});
        }

        function syncChannelById(channelId) {
            const thread = getThread(channelId);
            if (!thread) {
                return;
            }
            const sessions = presence?.state?.sessionsByChannelId?.get(channelId) || [];
            const wantedRtcIds = new Set();
            for (const s of sessions) {
                wantedRtcIds.add(toRtcSessionId(s.id));
                ensureRtcSessionFromPresence(s);
            }

            // Remove stale synthetic sessions for this thread.
            for (const rtcSession of thread.rtcSessions || []) {
                if (rtcSession.id < 0 && !wantedRtcIds.has(rtcSession.id)) {
                    try {
                        if (rtcSession.raisingHand) {
                            env.services["discuss.rtc"]?.removeCallNotification?.("raise_hand_" + rtcSession.id);
                        }
                    } catch (e) {
                        warn("Failed to remove raise hand notification:", e);
                    }
                    rtcSession.delete();
                }
            }
        }

        function findPresenceSession(channelId, identity) {
            const sessions = presence?.state?.sessionsByChannelId?.get(channelId) || [];
            const {partnerId, guestId} = parseLivekitIdentity(identity);
            if (partnerId) {
                return sessions.find((s) => Number(s.partnerId) === partnerId);
            }
            if (guestId) {
                return sessions.find((s) => Number(s.guestId) === guestId);
            }
            return undefined;
        }

        function setStreamForIdentity(channelId, identity, {type = "camera", mediaStreamTrack} = {}) {
            if (!mediaStreamTrack) {
                return;
            }
            const s = findPresenceSession(channelId, identity);
            if (!s) {
                return;
            }
            ensureRtcSessionFromPresence(s);
            const rtcSession = store.RtcSession.get(toRtcSessionId(s.id));
            if (!rtcSession) {
                return;
            }
            try {
                const stream = new window.MediaStream();
                stream.addTrack(mediaStreamTrack);
                const next = new Map(rtcSession.videoStreams);
                next.set(type, stream);
                rtcSession.videoStreams = next;
                rtcSession.updateStreamState(type, true);
            } catch (e) {
                console.warn("setStreamForIdentity failed", e);
            }
        }

        function setLivekitVideoTrackForIdentity(channelId, identity, {type = "camera", track} = {}) {
            if (!track) {
                return;
            }
            const s = findPresenceSession(channelId, identity);
            if (!s) {
                return;
            }
            ensureRtcSessionFromPresence(s);
            const rtcSessionId = toRtcSessionId(s.id);
            livekitVideoTracks.set(trackKey(rtcSessionId, type), track);
        }

        function removeStreamForIdentity(channelId, identity, {type = "camera"} = {}) {
            const s = findPresenceSession(channelId, identity);
            if (!s) {
                return;
            }
            const rtcSession = store.RtcSession.get(toRtcSessionId(s.id));
            if (!rtcSession) {
                return;
            }
            const next = new Map(rtcSession.videoStreams);
            next.delete(type);
            rtcSession.videoStreams = next;
            rtcSession.updateStreamState(type, false);
        }

        function removeLivekitVideoTrackForIdentity(channelId, identity, {type = "camera"} = {}) {
            const s = findPresenceSession(channelId, identity);
            if (!s) {
                return;
            }
            const rtcSessionId = toRtcSessionId(s.id);
            livekitVideoTracks.delete(trackKey(rtcSessionId, type));
        }

        function getLivekitVideoTrack(rtcSessionId, type = "camera") {
            return livekitVideoTracks.get(trackKey(rtcSessionId, type));
        }

        function clearLivekitTracksForChannel(channelId) {
            const thread = getThread(channelId);
            if (!thread) {
                return;
            }
            const ids = (thread.rtcSessions || []).map((s) => s?.id).filter((id) => typeof id === "number" && id < 0);
            for (const rtcSessionId of ids) {
                livekitVideoTracks.delete(trackKey(rtcSessionId, "camera"));
                livekitVideoTracks.delete(trackKey(rtcSessionId, "screen"));
            }
        }

        function setLivekitVideoTrackForRtcSessionId(rtcSessionId, {type = "camera", track} = {}) {
            if (!rtcSessionId || !track) {
                return;
            }
            livekitVideoTracks.set(trackKey(rtcSessionId, type), track);
        }

        function removeLivekitVideoTrackForRtcSessionId(rtcSessionId, {type = "camera"} = {}) {
            if (!rtcSessionId) {
                return;
            }
            livekitVideoTracks.delete(trackKey(rtcSessionId, type));
        }

        function setStreamForRtcSessionId(rtcSessionId, {type = "camera", mediaStreamTrack} = {}) {
            if (!rtcSessionId || !mediaStreamTrack) {
                return;
            }
            const rtcSession = store.RtcSession.get(rtcSessionId);
            if (!rtcSession) {
                return;
            }
            try {
                const stream = new window.MediaStream();
                stream.addTrack(mediaStreamTrack);
                const next = new Map(rtcSession.videoStreams);
                next.set(type, stream);
                rtcSession.videoStreams = next;
                rtcSession.updateStreamState(type, true);
            } catch (e) {
                console.warn("setStreamForRtcSessionId failed", e);
            }
        }

        function removeStreamForRtcSessionId(rtcSessionId, {type = "camera"} = {}) {
            if (!rtcSessionId) {
                return;
            }
            const rtcSession = store.RtcSession.get(rtcSessionId);
            if (!rtcSession) {
                return;
            }
            const next = new Map(rtcSession.videoStreams);
            next.delete(type);
            rtcSession.videoStreams = next;
            rtcSession.updateStreamState(type, false);
        }

        function updateTalkingStates(channelId, identities = []) {
            if (!channelId) {
                return;
            }
            const speakers = new Set(Array.isArray(identities) ? identities : []);
            const sessions = presence?.state?.sessionsByChannelId?.get(channelId) || [];
            for (const s of sessions) {
                const rtcSessionId = toRtcSessionId(s.id);
                ensureRtcSessionFromPresence(s);
                const rtcSession = store.RtcSession.get(rtcSessionId);
                if (!rtcSession) {
                    continue;
                }
                const identity = s.partnerId ? `partner_${s.partnerId}` : s.guestId ? `guest_${s.guestId}` : undefined;
                const nextIsTalking = identity ? speakers.has(identity) : false;
                if (rtcSession.isTalking !== nextIsTalking) {
                    rtcSession.isTalking = nextIsTalking;
                }
            }
        }

        function enterCall(channelId, selfLivekitSessionId) {
            const thread = getThread(channelId);
            const rtc = env.services["discuss.rtc"];
            if (!thread || !rtc) {
                return;
            }
            rtc.state.channel = thread;
            // LiveKit is always server-based media, so mimic the base "server" call mode.
            // This impacts which participant tile shows connection-state warnings.
            rtc.state.connectionType = CONNECTION_TYPES.SERVER;
            if (selfLivekitSessionId) {
                const rtcSessionId = toRtcSessionId(selfLivekitSessionId);
                const selfSession = store.RtcSession.get(rtcSessionId);
                if (selfSession) {
                    rtc.selfSession = selfSession;
                }
            }
        }

        function exitCall(channelId) {
            const rtc = env.services["discuss.rtc"];
            const thread = getThread(channelId);
            if (!rtc || !thread) {
                return;
            }
            if (rtc.state.channel && rtc.state.channel.eq(thread)) {
                // Only clear client-side RTC state; LiveKit handles the actual media teardown.
                rtc.clear();
            }

            // Ensure we don't retain old LiveKit track objects across calls.
            clearLivekitTracksForChannel(channelId);
        }

        // Keep synthetic RTC sessions in sync with LiveKit presence updates.
        bus.subscribe("discuss.channel.livekit.session/update", (payload) => {
            const channelId = payload?.channelId;
            if (!channelId) {
                return;
            }
            // Presence service already updated its reactive map; we just mirror it.
            syncChannelById(channelId);
        });

        bus.subscribe("discuss.channel.livekit.session/ended", (payload) => {
            const channelId = payload?.channelId;
            const sessionId = payload?.sessionId;
            if (!channelId || !sessionId) {
                return;
            }

            try {
                const rtc = env.services["discuss.rtc"];
                if (rtc?.selfSession?.id === toRtcSessionId(sessionId)) {
                    if (typeof rtc.endCall === "function") {
                        rtc.endCall();
                    }
                    env.services.notification.add(_t("Disconnected from the RTC call by the server"), {
                        type: "warning",
                    });
                }
            } catch (e) {
                warn("Failed to handle session ended event:", e);
            }
            const rtcSession = store.RtcSession.get(toRtcSessionId(sessionId));
            if (rtcSession) {
                try {
                    if (rtcSession.raisingHand) {
                        const rtc = env.services["discuss.rtc"];
                        if (rtc && typeof rtc.removeCallNotification === "function") {
                            rtc.removeCallNotification("raise_hand_" + rtcSession.id);
                        }
                    }
                } catch (e) {
                    warn("Failed to remove raise hand notification on session end:", e);
                }
                rtcSession.delete();
            }
        });

        // Mimic base RTC incoming call semantics: trigger ringing invitations.
        bus.subscribe("discuss.channel.livekit.call/invitation", (payload) => {
            const channelId = payload?.channelId;
            const inviterSessionId = payload?.inviterSessionId;
            if (!channelId || !inviterSessionId) {
                return;
            }

            try {
                const thread = getThread(channelId);
                if (!thread) {
                    return;
                }

                // Don't ring if already in-call in this thread.
                if (thread.activeRtcSession) {
                    return;
                }

                // Don't ring the inviter.
                const selfLivekitSessionId = presence?.state?.selfSessionIdByChannelId?.get(channelId);
                if (selfLivekitSessionId && Number(selfLivekitSessionId) === Number(inviterSessionId)) {
                    return;
                }

                // Ensure synthetic sessions exist before attaching the invitation.
                syncChannelById(channelId);

                const inviterRtcSession = store.RtcSession.get(toRtcSessionId(inviterSessionId));
                if (!inviterRtcSession) {
                    return;
                }

                // Assigning this triggers stock UI + ringing sound via store.ringingThreads.
                thread.rtcInvitingSession = inviterRtcSession;
            } catch (e) {
                warn("Failed to apply LiveKit call invitation:", e);
            }
        });

        return {
            syncChannelById,
            enterCall,
            exitCall,
            updateTalkingStates,
            setStreamForIdentity,
            removeStreamForIdentity,
            setLivekitVideoTrackForIdentity,
            removeLivekitVideoTrackForIdentity,
            getLivekitVideoTrack,
            setLivekitVideoTrackForRtcSessionId,
            removeLivekitVideoTrackForRtcSessionId,
            setStreamForRtcSessionId,
            removeStreamForRtcSessionId,
            clearLivekitTracksForChannel,
        };
    },
};

registry.category("services").add("discuss.livekit_rtc_adapter", livekitRtcAdapterService);
