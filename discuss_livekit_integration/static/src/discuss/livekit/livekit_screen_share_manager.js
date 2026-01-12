/** @odoo-module */

/**
 * Screen share manager for LiveKit.
 * Owns enable/disable logic and bridges local screen-share tracks into the native call UI.
 */
export class LivekitScreenShareManager {
    constructor(env, state, warn, publicationToType, getLivekitClient) {
        this.env = env;
        this.state = state;
        this.warn = warn;
        this.publicationToType = publicationToType;
        this.getLivekitClient = getLivekitClient;
    }

    async _enableScreenShareFallback(localParticipant, LivekitClient) {
        // Fallback: create a screen share track and publish it.
        const createFn = LivekitClient?.createLocalScreenTracks || LivekitClient?.createLocalTracks || null;
        if (typeof createFn !== "function") {
            throw new Error("LiveKit screen share not supported by this SDK build");
        }
        const tracks = await createFn({audio: false, video: true, screen: true});
        for (const t of tracks || []) {
            if (t?.kind === "video") {
                await localParticipant.publishTrack(t, {
                    source: LivekitClient?.Track?.Source?.ScreenShare || LivekitClient?.TrackSource?.ScreenShare || "screen_share",
                });
            }
        }
    }

    async _disableScreenShareFallback(localParticipant) {
        // Best-effort unpublish any existing screen share tracks.
        if (!localParticipant?.videoTrackPublications) {
            return;
        }
        for (const pub of localParticipant.videoTrackPublications.values()) {
            if (this.publicationToType(pub) === "screen") {
                try {
                    await localParticipant.unpublishTrack(pub.track);
                } catch (e) {
                    this.warn("Failed to unpublish screen share:", e);
                }
            }
        }
    }

    _bridgeLocalScreenShareTracksToNativeUi() {
        try {
            const adapter = this.env.services["discuss.livekit_rtc_adapter"];
            const channelId = this.state.channel?.id;
            const room = this.state.room;
            if (!adapter || !channelId || !room) {
                return;
            }
            const identity = room.localParticipant.identity;

            if (!this.state.screenShareEnabled) {
                adapter.removeLivekitVideoTrackForIdentity(channelId, identity, {type: "screen"});
                adapter.removeStreamForIdentity(channelId, identity, {type: "screen"});
                return;
            }

            const pubs = room.localParticipant.videoTrackPublications?.values?.();
            if (!pubs) {
                return;
            }

            for (const pub of pubs) {
                const track = pub?.track;
                if (!track?.mediaStreamTrack) {
                    continue;
                }
                const type = this.publicationToType(pub);
                if (type !== "screen") {
                    continue;
                }
                adapter.setLivekitVideoTrackForIdentity(channelId, identity, {
                    type: "screen",
                    track,
                });
                adapter.setStreamForIdentity(channelId, identity, {
                    type: "screen",
                    mediaStreamTrack: track.mediaStreamTrack,
                });
            }
        } catch {
            // Ignore
        }
    }

    async setScreenShareEnabled(enabled) {
        if (!this.state.room) {
            return;
        }

        const LivekitClient = this.getLivekitClient();
        this.state.screenShareEnabled = Boolean(enabled);

        // Prefer built-in helper if available.
        try {
            const localParticipant = this.state.room.localParticipant;
            if (typeof localParticipant?.setScreenShareEnabled === "function") {
                await localParticipant.setScreenShareEnabled(this.state.screenShareEnabled);
            } else if (this.state.screenShareEnabled) {
                await this._enableScreenShareFallback(localParticipant, LivekitClient);
            } else {
                await this._disableScreenShareFallback(localParticipant);
            }
        } catch (e) {
            this.warn("setScreenShareEnabled failed", e);
            this.env.services.notification.add(`Screen share failed: ${e?.message || e}`, {
                type: "danger",
            });
            this.state.screenShareEnabled = false;
        }

        const presence = this.env.services["discuss.livekit_presence"];
        if (this.state.channel && this.state.isHost) {
            await presence?.updatePresence(this.state.channel, {
                is_screen_sharing_on: this.state.screenShareEnabled,
            });
        }

        this._bridgeLocalScreenShareTracksToNativeUi();
    }
}
