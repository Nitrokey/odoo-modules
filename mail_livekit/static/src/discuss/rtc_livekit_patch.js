/** @odoo-module */

import {Rtc} from "@mail/discuss/call/common/rtc_service";
import {patch} from "@web/core/utils/patch";

function exitFullscreen(fullscreen) {
    if (fullscreen && typeof fullscreen.exit === "function") {
        fullscreen.exit();
    }
}

async function leaveLivekitCall({livekit, adapter, channelId, fullscreen}) {
    exitFullscreen(fullscreen);
    await livekit.leave();
    if (adapter && typeof adapter.exitCall === "function") {
        adapter.exitCall(channelId);
    }
    if (adapter && typeof adapter.clearLivekitTracksForChannel === "function") {
        adapter.clearLivekitTracksForChannel(channelId);
    }
}

function getPresenceSessions(presence, channel) {
    if (!presence || typeof presence.getSessions !== "function") {
        return [];
    }
    return presence.getSessions(channel) || [];
}

function getEffectiveCameraFromOngoingSessions({presence, channel, camera}) {
    const sessions = getPresenceSessions(presence, channel);
    const ongoingHasVideo = sessions.some((s) =>
        Boolean(s?.isCameraOn || s?.isScreenSharingOn)
    );
    return Boolean(camera || ongoingHasVideo);
}

function enterNativeCallSafely({adapter, presence, channel}) {
    try {
        if (adapter && typeof adapter.syncChannelById === "function") {
            adapter.syncChannelById(channel.id);
        }
        if (adapter && typeof adapter.enterCall === "function") {
            adapter.enterCall(
                channel.id,
                presence?.state?.selfSessionIdByChannelId?.get(channel.id)
            );
        }
        // Mimic base RTC behavior: accepting/joining cancels the ringing invitation.
        channel.rtcInvitingSession = undefined;
    } catch {
        // Ignore
    }
}

patch(Rtc.prototype, {
    async toggleCall(channel, {audio = true, fullscreen, camera} = {}) {
        // If LiveKit is active, bypass Odoo RTC and use the LiveKit service.
        const livekit = this.store.env.services["discuss.livekit"];
        const adapter = this.store.env.services["discuss.livekit_rtc_adapter"];
        const presence = this.store.env.services["discuss.livekit_presence"];
        if (!livekit) {
            return await super.toggleCall(channel, {
                audio,
                fullscreen,
                camera,
            });
        }
        if (this.state.hasPendingRequest) {
            return;
        }
        const isActiveLivekitCall = livekit.isInCall(channel);
        const previousChannel = livekit.state.channel;
        if (previousChannel) {
            if (!isActiveLivekitCall) {
                await leaveLivekitCall({
                    livekit,
                    adapter,
                    channelId: previousChannel.id,
                    fullscreen,
                });
                // Ensure native RTC UI/state is fully torn down before joining another call.
                super.endCall(previousChannel);
            }
        }
        if (isActiveLivekitCall) {
            await leaveLivekitCall({
                livekit,
                adapter,
                channelId: channel?.id,
                fullscreen,
            });
            return super.endCall(channel);
        }

        const effectiveCamera = getEffectiveCameraFromOngoingSessions({
            presence,
            channel,
            camera,
        });
        const ok = await livekit.join(channel, {
            audio,
            camera: effectiveCamera,
        });
        if (!ok) {
            return;
        }
        enterNativeCallSafely({adapter, presence, channel});
        // Play the outgoing call sound to match base RTC behavior
        this.soundEffectsService.play("channel-join");
    },

    async joinCall(channel, {audio = true, camera = false} = {}) {
        const livekit = this.store.env.services["discuss.livekit"];
        const adapter = this.store.env.services["discuss.livekit_rtc_adapter"];
        const presence = this.store.env.services["discuss.livekit_presence"];
        if (!livekit) {
            return await super.joinCall(channel, {audio, camera});
        }
        const effectiveCamera = getEffectiveCameraFromOngoingSessions({
            presence,
            channel,
            camera,
        });
        const ok = await livekit.join(channel, {
            audio,
            camera: effectiveCamera,
        });
        if (!ok) {
            return;
        }
        enterNativeCallSafely({adapter, presence, channel});
        // Play the outgoing call sound to match base RTC behavior
        this.soundEffectsService.play("channel-join");
    },

    async leaveCall(channel = this.state.channel) {
        const livekit = this.store.env.services["discuss.livekit"];
        const adapter = this.store.env.services["discuss.livekit_rtc_adapter"];
        if (!livekit) {
            return await super.leaveCall(channel);
        }
        await livekit.leave();
        if (adapter && typeof adapter.exitCall === "function") {
            adapter.exitCall(channel?.id);
        }
        // Ensure RTC internal state is cleaned up.
        return super.endCall(channel);
    },

    endCall(channel = this.state.channel) {
        const livekit = this.store.env.services["discuss.livekit"];
        const adapter = this.store.env.services["discuss.livekit_rtc_adapter"];
        if (livekit) {
            livekit.leave();
            if (adapter && typeof adapter.exitCall === "function") {
                adapter.exitCall(channel?.id);
            }
            return super.endCall(channel);
        }
        return super.endCall(channel);
    },

    // Prevent Odoo's RTC background loop from making RTC calls while LiveKit is active.
    async ping() {
        const livekit = this.store.env.services["discuss.livekit"];
        if (livekit?.state?.connected) {
            return;
        }
        return await super.ping();
    },

    async call(options = {}) {
        const livekit = this.store.env.services["discuss.livekit"];
        if (livekit?.state?.connected) {
            return;
        }
        return await super.call(options);
    },

    deleteSession(id) {
        // Synthetic LiveKit sessions use negative IDs; never attempt WebRTC teardown.
        if (typeof id === "number" && id < 0) {
            const session = this.store.RtcSession.get(id);
            if (session) {
                session.delete();
            }
            return;
        }
        return super.deleteSession(id);
    },

    async mute() {
        const livekit = this.store.env.services["discuss.livekit"];
        if (!livekit?.state?.connected) {
            return await super.mute();
        }
        if (livekit.state.micEnabled) {
            await livekit.toggleMic();
        }
    },

    async unmute() {
        const livekit = this.store.env.services["discuss.livekit"];
        if (!livekit?.state?.connected) {
            return await super.unmute();
        }
        if (!livekit.state.micEnabled) {
            await livekit.toggleMic();
        }
    },

    async setMute(isSelfMuted) {
        const livekit = this.store.env.services["discuss.livekit"];
        if (!livekit?.state?.connected) {
            return await super.setMute(isSelfMuted);
        }
        // In LiveKit mode, muting means disabling the microphone.
        if (typeof livekit.setMicEnabled === "function") {
            await livekit.setMicEnabled(!isSelfMuted);
        }
    },

    async setTalking(isTalking) {
        const livekit = this.store.env.services["discuss.livekit"];
        if (!livekit?.state?.connected) {
            return await super.setTalking(isTalking);
        }
        // Update the visual state
        if (this.selfSession) {
            this.selfSession.isTalking = isTalking;
        }
        // Notify the push-to-talk extension if present
        const pttExtService = this.store.env.services["discuss.pttExtension"];
        if (pttExtService && typeof pttExtService.notifyIsTalking === "function") {
            pttExtService.notifyIsTalking(Boolean(isTalking));
        }
        // Control the LiveKit microphone
        if (typeof livekit.setMicEnabled === "function") {
            await livekit.setMicEnabled(Boolean(isTalking));
        }
    },

    async setDeaf(isDeaf) {
        const livekit = this.store.env.services["discuss.livekit"];
        if (!livekit?.state?.connected) {
            return await super.setDeaf(isDeaf);
        }
        if (typeof livekit.setDeaf === "function") {
            await livekit.setDeaf(Boolean(isDeaf));
        }
    },

    async raiseHand(raise) {
        const livekit = this.store.env.services["discuss.livekit"];
        if (!livekit?.state?.connected) {
            return await super.raiseHand(raise);
        }
        const toOdooDatetime = (d) => {
            // Odoo fields.Datetime expects: "YYYY-MM-DD HH:MM:SS".
            // Use UTC to keep ordering stable across clients.
            const pad2 = (n) => String(n).padStart(2, "0");
            return (
                d.getUTCFullYear() +
                "-" +
                pad2(d.getUTCMonth() + 1) +
                "-" +
                pad2(d.getUTCDate()) +
                " " +
                pad2(d.getUTCHours()) +
                ":" +
                pad2(d.getUTCMinutes()) +
                ":" +
                pad2(d.getUTCSeconds())
            );
        };
        const channel = livekit.state.channel || this.state.channel;
        const presence = this.store.env.services["discuss.livekit_presence"];
        const active = Boolean(raise);
        const ts = active ? new Date() : undefined;
        if (this.selfSession) {
            this.selfSession.raisingHand = ts;
        }
        if (channel) {
            if (presence && typeof presence.updatePresence === "function") {
                await presence.updatePresence(channel, {
                    raising_hand: active ? toOdooDatetime(ts) : false,
                });
            }
        }
    },

    async toggleVideo(type, force) {
        const livekit = this.store.env.services["discuss.livekit"];
        if (!livekit?.state?.connected) {
            return await super.toggleVideo(type, force);
        }
        if (type === "camera") {
            const enabled = force ?? !livekit.state.cameraEnabled;
            if (typeof livekit.setCameraEnabled === "function") {
                await livekit.setCameraEnabled(Boolean(enabled));
            }
            return;
        }
        if (type === "screen") {
            const enabled = force ?? !livekit.state.screenShareEnabled;
            if (typeof livekit.setScreenShareEnabled === "function") {
                await livekit.setScreenShareEnabled(Boolean(enabled));
            }
            return;
        }
        return;
    },
});
