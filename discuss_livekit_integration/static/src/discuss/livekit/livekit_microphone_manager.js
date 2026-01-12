/** @odoo-module */

import {getLivekitClient} from "./livekit_sdk_loader";

export class LivekitMicrophoneManager {
    constructor(env, state, warn, log) {
        this.env = env;
        this.state = state;
        this.warn = warn;
        this.log = log;

        this.micOp = Promise.resolve();
        this.localPublishedMicrophoneTrack = null;
    }

    _getStoreSettings() {
        const store = this.env.services["mail.store"];
        return store?.settings || null;
    }

    _getSelectedDeviceId() {
        const settings = this._getStoreSettings();
        const id = settings?.audioInputDeviceId;
        return typeof id === "string" ? id : "";
    }

    withMicLock(fn) {
        this.micOp = this.micOp.then(fn, fn);
        return this.micOp;
    }

    async _createLocalMicrophoneTrack() {
        const LivekitClient = getLivekitClient();
        if (!LivekitClient?.createLocalAudioTrack) {
            throw new Error("LiveKit client missing createLocalAudioTrack");
        }

        // Important: LiveKit internally deep-clones options via structuredClone.
        // Keep this object strictly data-only (no proxies) to avoid DataCloneError.
        const deviceId = this._getSelectedDeviceId();
        const options = {
            echoCancellation: true,
            noiseSuppression: true,
            ...(deviceId ? {deviceId} : {}),
        };
        return await LivekitClient.createLocalAudioTrack(options);
    }

    async _unpublishMicrophoneTrack(track, {stopTrack = false} = {}) {
        if (!this.state.room || !track) {
            return;
        }
        try {
            await this.state.room.localParticipant.unpublishTrack(track);
        } catch {
            // Ignore
        }
        if (!stopTrack) {
            return;
        }
        try {
            if (typeof track.stop === "function") {
                track.stop();
            }
        } catch {
            // Ignore
        }
    }

    async _publishMicrophoneTrack(track) {
        if (!this.state.room) {
            return;
        }
        const LivekitClient = getLivekitClient();
        const micSource = LivekitClient?.Track?.Source?.Microphone || LivekitClient?.TrackSource?.Microphone;
        const publishOpts = micSource ? {source: micSource} : undefined;
        await this.state.room.localParticipant.publishTrack(track, publishOpts);
    }

    async setMicrophoneEnabled(enabled) {
        return this.withMicLock(async () => {
            if (!this.state.room) {
                return;
            }

            const shouldEnable = Boolean(enabled);

            if (!shouldEnable) {
                await this._unpublishMicrophoneTrack(this.localPublishedMicrophoneTrack, {stopTrack: true});
                this.localPublishedMicrophoneTrack = null;
                this.state.micEnabled = false;
                return;
            }

            // Create/publish first; then swap out the old track to avoid going silent if creation fails.
            let nextTrack = null;
            try {
                nextTrack = await this._createLocalMicrophoneTrack();
                await this._publishMicrophoneTrack(nextTrack);
            } catch (e) {
                this.warn("microphone enable failed", e);
                try {
                    if (nextTrack && typeof nextTrack.stop === "function") {
                        nextTrack.stop();
                    }
                } catch {
                    // Ignore
                }
                throw e;
            }

            const prev = this.localPublishedMicrophoneTrack;
            this.localPublishedMicrophoneTrack = nextTrack;
            this.state.micEnabled = true;

            // Remove the previous mic track after the new one is live.
            if (prev && prev !== nextTrack) {
                await this._unpublishMicrophoneTrack(prev, {stopTrack: true});
            }
        });
    }

    async restartMicrophoneWithSelectedDevice() {
        return this.withMicLock(async () => {
            if (!this.state.room || !this.state.connected) {
                return;
            }
            if (!this.state.micEnabled) {
                return;
            }

            const deviceId = this._getSelectedDeviceId();
            this.log("Restarting microphone with selected device", {deviceId});

            // Recreate track based on updated constraints/deviceId.
            let nextTrack = null;
            try {
                nextTrack = await this._createLocalMicrophoneTrack();
                await this._publishMicrophoneTrack(nextTrack);
            } catch (e) {
                this.warn("microphone device switch failed", e);
                try {
                    if (nextTrack && typeof nextTrack.stop === "function") {
                        nextTrack.stop();
                    }
                } catch {
                    // Ignore
                }
                throw e;
            }

            const prev = this.localPublishedMicrophoneTrack;
            this.localPublishedMicrophoneTrack = nextTrack;

            if (prev && prev !== nextTrack) {
                await this._unpublishMicrophoneTrack(prev, {stopTrack: true});
            }
        });
    }

    async cleanup() {
        await this.withMicLock(async () => {
            await this._unpublishMicrophoneTrack(this.localPublishedMicrophoneTrack, {stopTrack: true});
            this.localPublishedMicrophoneTrack = null;
        });
    }
}
