/** @odoo-module */

import {HEARTBEAT_INTERVAL_MS} from "./livekit_utils";
import {reactive} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

export const livekitPresenceService = {
    dependencies: ["bus_service", "notification"],
    async start(env, services) {
        // On some pages (notably public/guest discuss), the bus worker may not be started yet.
        // We explicitly start it to make sure our presence notifications can be received.
        try {
            await services.bus_service.start();
        } catch {
            // Best-effort: if the bus cannot start here, other mail services may still start it.
        }

        const state = reactive({
            /** @type {Map<number, any[]>} channelId -> sessions[] */
            sessionsByChannelId: reactive(new Map()),
            /** @type {Map<number, number>} channelId -> selfSessionId */
            selfSessionIdByChannelId: reactive(new Map()),
        });

        /** @type {Map<number, number>} channelId -> intervalId */
        const heartbeatIntervalByChannelId = new Map();

        function _stopHeartbeat(channelId) {
            const handle = heartbeatIntervalByChannelId.get(channelId);
            if (handle) {
                clearInterval(handle);
                heartbeatIntervalByChannelId.delete(channelId);
            }
        }

        function _applySnapshot(channelId, sessions) {
            state.sessionsByChannelId.set(channelId, sessions || []);
        }

        function _applyUpdate({channelId, action, sessions}) {
            const current = state.sessionsByChannelId.get(channelId) || [];
            const byId = new Map(current.map((s) => [s.id, s]));
            if (action === "ADD" || action === "UPDATE") {
                for (const s of sessions || []) {
                    byId.set(s.id, s);
                }
            } else if (action === "DELETE") {
                for (const s of sessions || []) {
                    byId.delete(s.id);
                }
            }
            state.sessionsByChannelId.set(channelId, Array.from(byId.values()));
        }

        function _startHeartbeat(channelId) {
            _stopHeartbeat(channelId);
            // Keep-alive slightly faster than the backend inactivity cutoff (1m15).
            const handle = setInterval(async () => {
                try {
                    const selfSessionId = state.selfSessionIdByChannelId.get(channelId);
                    if (!selfSessionId) {
                        _stopHeartbeat(channelId);
                        return;
                    }
                    const sessions = state.sessionsByChannelId.get(channelId) || [];
                    const checkIds = sessions.map((s) => s.id);
                    const res = await rpc("/discuss/livekit/channel/ping", {
                        channel_id: channelId,
                        livekit_session_id: selfSessionId,
                        check_session_ids: checkIds,
                    });
                    if (res?.sessions) {
                        _applySnapshot(channelId, res.sessions);
                    }
                    if (res?.outdatedSessionIds?.length) {
                        _applyUpdate({
                            channelId,
                            action: "DELETE",
                            sessions: res.outdatedSessionIds.map((id) => ({id})),
                        });
                    }
                } catch {
                    // Ignore: offline / transient errors; backend GC will eventually kick in
                }
            }, HEARTBEAT_INTERVAL_MS);
            heartbeatIntervalByChannelId.set(channelId, handle);
        }

        // LiveKit presence updates are broadcast by our addon model.
        services.bus_service.subscribe("discuss.channel.livekit.session/update", (payload) => {
            try {
                _applyUpdate(payload);
            } catch (e) {
                env.services.notification.add(`LiveKit presence update failed: ${e?.message || e}`, {
                    type: "warning",
                });
            }
        });

        services.bus_service.subscribe("discuss.channel.livekit.session/ended", (payload) => {
            const sessionId = payload?.sessionId;
            if (!sessionId) {
                return;
            }
            // Best-effort removal from all channels.
            for (const [channelId, sessions] of state.sessionsByChannelId.entries()) {
                const next = (sessions || []).filter((s) => s.id !== sessionId);
                if (next.length !== (sessions || []).length) {
                    state.sessionsByChannelId.set(channelId, next);
                }
            }
        });

        async function updatePresence(channel, values) {
            const sessionId = state.selfSessionIdByChannelId.get(channel.id);
            if (!sessionId) {
                return;
            }
            await rpc("/mail/livekit/session/update_and_broadcast", {
                session_id: sessionId,
                values,
            });
        }

        async function joinPresence(channel, {camera = false, audio = true} = {}) {
            const res = await rpc("/mail/livekit/channel/join_call", {
                channel_id: channel.id,
                camera,
            });
            state.selfSessionIdByChannelId.set(channel.id, res.selfSessionId);
            _applySnapshot(channel.id, res.sessions);
            _startHeartbeat(channel.id);
            // Reflect initial mute state (backend stores is_muted)
            await updatePresence(channel, {is_muted: !audio, is_camera_on: camera});
            return res;
        }

        async function leavePresence(channel) {
            await rpc("/mail/livekit/channel/leave_call", {channel_id: channel.id});
            _stopHeartbeat(channel.id);
            state.selfSessionIdByChannelId.delete(channel.id);
            // Keep any remaining sessions (other participants) so the UI can still show
            // that a call is ongoing. The server will broadcast the self-session deletion,
            // which will be applied via bus updates.
        }

        function getSessions(channel) {
            return state.sessionsByChannelId.get(channel.id) || [];
        }

        return {
            state,
            joinPresence,
            leavePresence,
            updatePresence,
            getSessions,
        };
    },
};

registry.category("services").add("discuss.livekit_presence", livekitPresenceService);
