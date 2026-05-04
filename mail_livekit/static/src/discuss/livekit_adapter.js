/** @odoo-module */

import {Source, livekitService} from "./livekit_service";

export class LiveKitAdapter {
    livekitService = null;
    _listeners = [];
    _isDisconnecting = false;

    getSfuConsumerStats() {
        return [];
    }

    addSfu() {
        return;
    }

    removeSfu() {
        return;
    }

    addEventListener(name, f) {
        this._listeners.push({name, f});
    }

    _emit(name, payload) {
        if (this._isDisconnecting) return;
        for (const {f} of this._listeners) {
            f({detail: {name, payload}});
        }
    }

    async updateUpload(source, track) {
        const livekitSource = Object.values(Source).includes(source)
            ? source
            : source === "audio"
              ? Source.MICROPHONE
              : source === "camera"
                ? Source.CAMERA
                : Source.SCREEN;
        await livekitService?.setTrackEnabled(livekitSource, Boolean(track), track);
    }

    updateDownload() {
        // Implement selective subscription if needed
    }

    updateInfo(info) {
        livekitService.publishInfo(info);
    }

    handleTrackSubscribed(participantId, source, track, audioElement = null) {
        if (track.kind === "audio") {
            return this._emit("setAudioVolume", {
                identity: participantId,
                element: audioElement,
            });
        }

        this._emit("trackSubscribed", {
            identity: participantId,
            type: source === Source.SCREEN ? "screen" : "camera",
            track: track,
        });
    }

    handleTrackMuted(participantId, source, track, muted) {
        console.debug("Track muted event:", participantId, source, track, muted);
        const type =
            source === Source.MICROPHONE
                ? "audio"
                : source === Source.SCREEN
                  ? "screen"
                  : "camera";
        if (muted) {
            return this._emit("track", {
                identity: participantId,
                type: type,
                track: track,
                active: false,
            });
        }
        return this.handleTrackSubscribed(participantId, source, track);
    }

    addLivekitListeners() {
        livekitService.subscribeToInfoChange("adapter", (info) => {
            console.debug("received Info change event:", info);
            this._emit("info_change", info);
        });
        livekitService.subscribeToTrackSubscribed(
            "adapter",
            (participantId, source, track, audioElement = null) => {
                console.debug(
                    "received Track subscribed event:",
                    participantId,
                    source,
                    track
                );
                this.handleTrackSubscribed(participantId, source, track, audioElement);
            }
        );
        livekitService.subscribeToTrackMuted(
            "adapter",
            (participantId, source, track, muted) => {
                console.debug(
                    "received Track muted event:",
                    participantId,
                    source,
                    track,
                    muted
                );
                this.handleTrackMuted(participantId, source, track, muted);
            }
        );
    }

    async connect(livekit_url, token) {
        this.addLivekitListeners();
        try {
            await livekitService?.connect(livekit_url, token);
        } catch (error) {
            await livekitService?.disconnect();
            throw error;
        }
    }

    async disconnect() {
        this._isDisconnecting = true;
        await livekitService?.disconnect();
        this._listeners = [];
        this._isDisconnecting = false;
    }

    isConnected() {
        return livekitService.connected;
    }
}
