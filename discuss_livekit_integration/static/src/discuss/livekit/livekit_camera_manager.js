/** @odoo-module */

import {
    ensureTrackProcessorsLoaded,
    getLivekitClient,
    getLivekitTrackProcessors,
} from "./livekit_sdk_loader";
import {BLUR_PROCESSOR_MAX_FPS} from "./livekit_utils";
import {onChange} from "@mail/utils/common/misc";

/**
 * Camera manager for LiveKit video tracks.
 * Handles camera creation, publishing, blur processing, and cleanup.
 */
export class LivekitCameraManager {
    constructor(env, state, warn, log) {
        this.env = env;
        this.state = state;
        this.warn = warn;
        this.log = log;
        this.localPublishedCameraTrack = null;
        this.cameraOp = Promise.resolve();

        this._setupBlurWatchers();
    }

    _getStoreSettings() {
        const store = this.env.services["mail.store"];
        return store?.settings || null;
    }

    _getPresenceService() {
        return this.env.services["discuss.livekit_presence"];
    }

    _isScreenShareSource(source) {
        // LiveKit source values can be enums or strings depending on build.
        return (
            source === "screen_share" ||
            source === "screenshare" ||
            source === "screen" ||
            source === "ScreenShare" ||
            source === "SCREEN_SHARE"
        );
    }

    _publicationToType(publication) {
        const src = publication?.source;
        return this._isScreenShareSource(src) ? "screen" : "camera";
    }

    _getTrackProcessor(track) {
        try {
            return typeof track?.getProcessor === "function"
                ? track.getProcessor()
                : null;
        } catch {
            return null;
        }
    }

    async _stopTrackProcessor(track) {
        if (typeof track?.stopProcessor !== "function") {
            return;
        }
        await track.stopProcessor(false);
    }

    async _stopProcessorIfAny(track) {
        const current = this._getTrackProcessor(track);
        if (!current) {
            return;
        }
        await this._stopTrackProcessor(track);
    }

    _setUseBlurSetting(value) {
        const settings = this._getStoreSettings();
        if (!settings) {
            return;
        }
        settings.useBlur = Boolean(value);
    }

    async _enableBlurOnTrack(track, {forceRecreate = false} = {}) {
        const processor = await this._createBackgroundBlurProcessor();
        if (forceRecreate) {
            await this._stopProcessorIfAny(track);
        }
        await track.setProcessor(processor);
    }

    async _disableBlurOnTrack(track) {
        await this._stopTrackProcessor(track);
    }

    _getAdapterContext() {
        const adapter = this.env.services["discuss.livekit_rtc_adapter"];
        const channelId = this.state.channel?.id;
        const room = this.state.room;
        if (!adapter || !channelId || !room) {
            return null;
        }
        const identity = room.localParticipant.identity;
        const rtc = this.env.services["discuss.rtc"];
        const selfRtcSessionId = rtc?.selfSession?.id;
        return {adapter, channelId, identity, selfRtcSessionId};
    }

    _callIfFn(obj, methodName, ...args) {
        const fn = obj?.[methodName];
        if (typeof fn === "function") {
            fn.apply(obj, args);
        }
    }

    _removeLocalCameraBridge(ctx) {
        const {adapter, channelId, identity, selfRtcSessionId} = ctx;
        if (selfRtcSessionId) {
            this._callIfFn(
                adapter,
                "removeLivekitVideoTrackForRtcSessionId",
                selfRtcSessionId,
                {type: "camera"}
            );
            this._callIfFn(adapter, "removeStreamForRtcSessionId", selfRtcSessionId, {
                type: "camera",
            });
        }
        this._callIfFn(
            adapter,
            "removeLivekitVideoTrackForIdentity",
            channelId,
            identity,
            {type: "camera"}
        );
        this._callIfFn(adapter, "removeStreamForIdentity", channelId, identity, {
            type: "camera",
        });
    }

    _setLocalCameraBridge(ctx, track) {
        const {adapter, channelId, identity, selfRtcSessionId} = ctx;
        if (selfRtcSessionId) {
            this._callIfFn(
                adapter,
                "setLivekitVideoTrackForRtcSessionId",
                selfRtcSessionId,
                {
                    type: "camera",
                    track,
                }
            );
        }
        this._callIfFn(
            adapter,
            "setLivekitVideoTrackForIdentity",
            channelId,
            identity,
            {type: "camera", track}
        );

        const mst = track?.mediaStreamTrack;
        if (!mst) {
            return;
        }
        if (selfRtcSessionId) {
            this._callIfFn(adapter, "setStreamForRtcSessionId", selfRtcSessionId, {
                type: "camera",
                mediaStreamTrack: mst,
            });
        }
        this._callIfFn(adapter, "setStreamForIdentity", channelId, identity, {
            type: "camera",
            mediaStreamTrack: mst,
        });
    }

    _setupBlurWatchers() {
        const store = this.env.services["mail.store"];
        if (!store?.settings) {
            return;
        }
        // If blur settings change while camera is on, apply/remove the LiveKit processor.
        try {
            onChange(store.settings, "useBlur", async () => {
                await this.withCameraLock(async () => {
                    await this._applyBlurFromSettings();
                });
            });
            onChange(
                store.settings,
                ["edgeBlurAmount", "backgroundBlurAmount"],
                async () => {
                    await this.withCameraLock(async () => {
                        // Only refresh processor if blur is enabled.
                        if (!store.settings.useBlur) {
                            return;
                        }
                        await this._applyBlurFromSettings({forceRecreate: true});
                    });
                }
            );
        } catch (e) {
            // Some environments may not provide onChange; ignore.
            this.warn("Failed to setup blur watchers:", e);
        }
    }

    async _applyBlurFromSettings({forceRecreate = false} = {}) {
        if (
            !this.state.connected ||
            !this.state.cameraEnabled ||
            !this.localPublishedCameraTrack
        ) {
            return;
        }

        const settings = this._getStoreSettings();
        if (!settings) {
            return;
        }

        const track = this.localPublishedCameraTrack;

        try {
            if (settings.useBlur) {
                await this._enableBlurOnTrack(track, {forceRecreate});
            } else {
                await this._disableBlurOnTrack(track);
            }
        } catch (e) {
            this.warn("blur toggle failed", e);
            try {
                this._setUseBlurSetting(false);
            } catch {
                // Ignore
            }
            try {
                await this._disableBlurOnTrack(track);
            } catch {
                // Ignore
            }
        } finally {
            await this.refreshLocalCameraBridge();
        }
    }

    /**
     * Serialize camera operations to avoid overlapping publish/unpublish cycles.
     * @param {Function} fn - The async function to execute
     * @returns {Promise} The result of the function
     */
    withCameraLock(fn) {
        this.cameraOp = this.cameraOp.then(fn, fn);
        return this.cameraOp;
    }

    /**
     * @returns {Number} The blur radius in pixels
     */
    _getBlurRadiusFromSettings() {
        const store = this.env.services["mail.store"];
        const raw = store?.settings?.backgroundBlurAmount;
        const value = typeof raw === "number" ? raw : parseFloat(String(raw));
        // LiveKit processors use a blur radius in pixels; pick a safe default.
        return Number.isFinite(value) && value > 0 ? value : 10;
    }

    /**
     * @returns {Promise<Object>} The background blur processor
     */
    async _createBackgroundBlurProcessor() {
        await ensureTrackProcessorsLoaded();
        const tp = getLivekitTrackProcessors();
        if (!tp) {
            throw new Error("Track processors not available");
        }
        const supported =
            (typeof tp.supportsBackgroundProcessors === "function" &&
                tp.supportsBackgroundProcessors()) ||
            (typeof tp.supportsModernBackgroundProcessors === "function" &&
                tp.supportsModernBackgroundProcessors());
        if (!supported) {
            throw new Error("Background blur not supported in this browser");
        }
        const radius = this._getBlurRadiusFromSettings();
        // BackgroundBlur(blurRadius, segmenterOptions, onFrameProcessed, processorOptions)
        return tp.BackgroundBlur(radius, undefined, undefined, {
            // Keep CPU/GPU load a bit lower than full camera FPS.
            maxFps: BLUR_PROCESSOR_MAX_FPS,
        });
    }

    /**
     * Create local camera track with optional blur processing
     * @returns {Promise<Object>} The created camera track
     */
    async _createLocalCameraTrack() {
        const LivekitClient = getLivekitClient();
        if (!LivekitClient?.createLocalVideoTrack) {
            throw new Error("LiveKit client missing createLocalVideoTrack");
        }

        const CAMERA_CONFIG = {
            width: 1280,
        };

        const lkTrack = await LivekitClient.createLocalVideoTrack(CAMERA_CONFIG);

        const store = this.env.services["mail.store"];
        if (store?.settings?.useBlur) {
            const processor = await this._createBackgroundBlurProcessor();
            await lkTrack.setProcessor(processor);
        }

        // If the underlying track ends (permissions revoked), shut camera off.
        try {
            const mediaStreamTrack = lkTrack.mediaStreamTrack;
            if (
                mediaStreamTrack &&
                typeof mediaStreamTrack.addEventListener === "function"
            ) {
                mediaStreamTrack.addEventListener("ended", () => {
                    this.withCameraLock(async () => {
                        await this._cleanupLocalCamera();
                        this.state.cameraEnabled = false;
                        const presence = this._getPresenceService();
                        if (
                            this.state.channel &&
                            this.state.isHost &&
                            typeof presence?.updatePresence === "function"
                        ) {
                            await presence.updatePresence(this.state.channel, {
                                is_camera_on: false,
                            });
                        }
                    }).catch((e) => this.warn("Camera track ended handler failed:", e));
                });
            }
        } catch (e) {
            this.warn("Failed to attach camera track ended listener:", e);
        }

        return lkTrack;
    }

    /**
     * @param {Object} options - Options for unpublishing
     * @param {Boolean} [options.stopTracks=false] - Whether to stop tracks
     */
    async _unpublishLocalCameraPublications({stopTracks = false} = {}) {
        if (!this.state.room) {
            return;
        }
        const lp = this.state.room.localParticipant;
        const pubs = Array.from(lp.videoTrackPublications?.values?.() || []);
        for (const pub of pubs) {
            if (this._publicationToType(pub) !== "camera") {
                continue;
            }
            const track = pub?.track;
            if (!track) {
                continue;
            }
            try {
                await lp.unpublishTrack(track);
            } catch {
                // Ignore
            }
            if (!stopTracks) {
                continue;
            }
            try {
                if (typeof track.stop === "function") {
                    track.stop();
                }
            } catch {
                // Ignore
            }
        }
    }

    async _cleanupLocalCamera() {
        try {
            await this._unpublishLocalCameraPublications({stopTracks: true});
        } catch (e) {
            this.warn("Failed to unpublish camera:", e);
        }
        try {
            // Pass false so LiveKit removes the hidden processor element.
            if (typeof this.localPublishedCameraTrack?.stopProcessor === "function") {
                await this.localPublishedCameraTrack.stopProcessor(false);
            }
        } catch (e) {
            this.warn("Failed to stop camera processor:", e);
        }
        try {
            if (typeof this.localPublishedCameraTrack?.stop === "function") {
                this.localPublishedCameraTrack.stop();
            }
        } catch (e) {
            this.warn("Failed to stop camera track:", e);
        }
        this.localPublishedCameraTrack = null;
    }

    async refreshLocalCameraBridge() {
        try {
            const ctx = this._getAdapterContext();
            if (!ctx) {
                return;
            }

            if (!this.state.cameraEnabled || !this.localPublishedCameraTrack) {
                this._removeLocalCameraBridge(ctx);
                return;
            }

            this._setLocalCameraBridge(ctx, this.localPublishedCameraTrack);
        } catch (e) {
            this.warn("Failed to refresh local camera bridge:", e);
        }
    }

    async setCameraEnabled(enabled) {
        return this.withCameraLock(async () => {
            if (!this.state.room) {
                return;
            }
            const shouldEnable = Boolean(enabled);

            if (shouldEnable) {
                try {
                    // Ensure any leftover camera tracks are removed first.
                    await this._unpublishLocalCameraPublications({stopTracks: false});
                    const track = await this._createLocalCameraTrack();
                    const LivekitClient = getLivekitClient();
                    const cameraSource =
                        LivekitClient?.Track?.Source?.Camera ||
                        LivekitClient?.TrackSource?.Camera;
                    const publishOpts = cameraSource
                        ? {source: cameraSource}
                        : undefined;
                    await this.state.room.localParticipant.publishTrack(
                        track,
                        publishOpts
                    );
                    this.localPublishedCameraTrack = track;
                    this.state.cameraEnabled = true;
                } catch (e) {
                    this.warn("camera enable failed", e);
                    this.env.services.notification.add(
                        `Camera failed: ${e?.message || e}`,
                        {
                            type: "warning",
                        }
                    );
                    // If blur was requested but failed to init, fall back gracefully.
                    const store = this.env.services["mail.store"];
                    if (store?.settings?.useBlur) {
                        try {
                            store.settings.useBlur = false;
                        } catch (err) {
                            this.warn("Failed to disable blur setting:", err);
                        }
                    }
                    await this._cleanupLocalCamera();
                    this.state.cameraEnabled = false;
                }
            } else {
                await this._cleanupLocalCamera();
                this.state.cameraEnabled = false;
            }

            const presence = this.env.services["discuss.livekit_presence"];
            // Only host should update presence
            if (this.state.channel && this.state.isHost) {
                if (typeof presence?.updatePresence === "function") {
                    await presence.updatePresence(this.state.channel, {
                        is_camera_on: this.state.cameraEnabled,
                    });
                }
            }

            await this.refreshLocalCameraBridge();
        });
    }

    async toggleCamera() {
        if (!this.state.room) {
            return;
        }
        await this.setCameraEnabled(!this.state.cameraEnabled);
    }

    async cleanup() {
        await this._cleanupLocalCamera();
    }
}
