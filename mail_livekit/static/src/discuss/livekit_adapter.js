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
        const livekitSource =
            source === "audio"
                ? Source.MICROPHONE
                : source === "camera"
                  ? Source.CAMERA
                  : Source.SCREEN;
        livekitService?.setTrackEnabled(livekitSource, Boolean(track), track);
    }

    updateDownload() {
        // Implement selective subscription if needed
    }

    updateInfo(info) {
        livekitService.publishInfo(info);
    }

    handleTrackSubscribed(participantId, source, track) {
        if (source === Source.MICROPHONE) {
            return this._emit("track", {
                sessionId: participantId,
                type: "audio",
                track: track?.mediaStreamTrack,
                active: !track?.isMuted,
            });
        }
        this._emit("trackSubscribed", {
            sessionId: participantId,
            type: source === Source.SCREEN ? "screen" : "camera",
            track: track,
        });
    }

    handleTrackMuted(participantId, source, track, muted) {
        const type =
            source === Source.MICROPHONE
                ? "audio"
                : source === Source.SCREEN
                  ? "screen"
                  : "camera";
        if (muted) {
            return this._emit("track", {
                sessionId: participantId,
                type: type,
                track: track,
                active: false,
            });
        }
        return this.handleTrackSubscribed(participantId, source, track);
    }

    addLivekitListeners() {
        livekitService.subscribeToInfoChange("adapter", (info) => {
            this._emit("info_change", info);
        });
        livekitService.subscribeToTrackSubscribed(
            "adapter",
            (participantId, source, track) =>
                this.handleTrackSubscribed(participantId, source, track)
        );
        livekitService.subscribeToTrackMuted(
            "adapter",
            (participantId, source, track, muted) =>
                this.handleTrackMuted(participantId, source, track, muted)
        );
    }

    async connect(livekit_url, token) {
        await livekitService?.connect(livekit_url, token);
        this.addLivekitListeners();
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
