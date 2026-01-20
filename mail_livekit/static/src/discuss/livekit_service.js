const {Room, VideoPresets, RoomEvent} = window.LivekitClient;

// This script should be the only contact point with Livekit SDK

let debug = false;

function log(...args) {
    if (debug) {
        console.log("[LivekitService]", ...args);
    }
}

class LivekitService {
    room = null;
    infoChangeListeners = new Map();
    trackSubscribedListeners = new Map();
    trackMutedListeners = new Map();
    containerElement = null;
    initiated = false;
    connected = false;

    _start() {
        const urlParams = new URLSearchParams(window.location.search);
        debug = urlParams.get("debug") !== null;
        log("LivekitService started with debug =", debug);
    }

    subscribeToTrackSubscribed(name, listener) {
        this.trackSubscribedListeners.set(name, listener);
    }

    handleTrackMuted(publication, participant) {
        log("Track muted", publication, participant);
        for (const listener of this.trackMutedListeners.values()) {
            listener(participant.identity, publication.source, publication.track, true);
        }
    }

    handleTrackUnmuted(publication, participant) {
        log("Track unmuted", publication, participant);
        for (const listener of this.trackMutedListeners.values()) {
            listener(
                participant.identity,
                publication.source,
                publication.track,
                false
            );
        }
    }

    handleTrackSubscribed(track, publication, participant) {
        log("Track subscribed", track, publication, participant);
        if (track.kind == "audio") {
            log("Attaching audio track to DOM");
            document.body.appendChild(track.attach());
        }
        for (const listener of this.trackSubscribedListeners.values()) {
            listener(participant.identity, publication.source, track);
        }
    }

    handleTrackUnsubscribed(track, publication, participant) {
        log("Track unsubscribed", track, publication, participant);
        track.detach();
        for (const listener of this.trackMutedListeners.values()) {
            listener(participant.identity, publication.source, publication.track, true);
        }
    }

    handleLocalTrackUnpublished(publication, participant) {
        log("Local track unpublished", publication, participant);
        publication.track.detach();
    }

    handleActiveSpeakerChange(speakers) {
        log("Active speakers changed", speakers);
    }

    handleDisconnect() {
        log("Disconnected from LiveKit room");
    }

    // Requires functions that accept info as parameter
    subscribeToInfoChange(name, listener) {
        log("Subscribing to info change:", name);
        this.infoChangeListeners.set(name, listener);
    }

    // Requires functions that accept info as parameter
    subscribeToTrackMuted(name, listener) {
        log("Subscribing to track muted:", name);
        this.trackMutedListeners.set(name, listener);
    }

    handleInfoChange(info) {
        log("Info change received:", info);
        for (const listener of this.infoChangeListeners.values()) {
            listener(info);
        }
    }

    async connect(url, token) {
        if (this.initiated || (this.room && this.room.isConnected)) {
            log("Already connected or connecting to LiveKit");
            return;
        }

        this.initiated = true;
        this._start();
        log("Connecting to LiveKit:", url);
        this.room = new Room({
            adaptiveStream: true,
            dynacast: true,
            videoCaptureDefaults: {
                resolution: VideoPresets.h720.resolution,
            },
        });

        this.room.prepareConnection(url, token);

        this.room
            .on(RoomEvent.TrackSubscribed, (...args) =>
                this.handleTrackSubscribed(...args)
            )
            .on(RoomEvent.TrackUnsubscribed, (...args) =>
                this.handleTrackUnsubscribed(...args)
            )
            .on(RoomEvent.ActiveSpeakersChanged, (...args) =>
                this.handleActiveSpeakerChange(...args)
            )
            .on(RoomEvent.Disconnected, (...args) => this.handleDisconnect(...args))
            .on(RoomEvent.LocalTrackUnpublished, (...args) =>
                this.handleLocalTrackUnpublished(...args)
            )
            .on(RoomEvent.DataReceived, (payload, participant) => {
                if (!participant) return;
                if (payload.byteLength === 0) return;
                const data = JSON.parse(new TextDecoder().decode(payload));
                if (data.type === "info_change") {
                    this.handleInfoChange({[participant.identity]: data.info});
                }
            })
            .on(RoomEvent.TrackMuted, (...args) => this.handleTrackMuted(...args))
            .on(RoomEvent.TrackUnmuted, (...args) => this.handleTrackUnmuted(...args))
            .on(RoomEvent.AudioPlaybackStatusChanged, () => {
                if (!this.room?.canPlaybackAudio) {
                    log("Issue with audi playback: requires UI interaction");
                }
            });

        try {
            await this.room.connect(url, token);
            log("Connected to LiveKit room");
            this.connected = true;
        } catch (error) {
            log("Failed to connect to LiveKit room:", error);
            this.room = null;
        }
    }

    async disconnect() {
        log("Clearing info change listeners");
        this.infoChangeListeners.clear();
        this.trackSubscribedListeners.clear();
        log("Disconnecting from LiveKit");
        await this.room?.disconnect();
        this.room = null;
        this.initiated = false;
        this.connected = false;
    }

    async setTrackEnabled(source, enabled, mediaStreamTrack = null) {
        log("Setting track enabled:", source, enabled, this.room);
        const publication = this.room?.localParticipant.getTrackPublication(source);

        if (mediaStreamTrack) {
            if (enabled && !publication) {
                log("Publishing new track for source:", source);
                await this.room?.localParticipant.publishTrack(mediaStreamTrack, {
                    source,
                    simulcast: true,
                });
            } else if (enabled && publication) {
                log("Replacing track for source:", source);
                await publication.track.replaceTrack(mediaStreamTrack);
                if (
                    mediaStreamTrack?.enabled ||
                    publication.track.source !==
                        window.LivekitClient.Track.Source.Microphone
                ) {
                    publication?.track?.unmute();
                }
            }
        } else if (publication) {
            log("Muting/unmuting existing track for source:", source);
            await publication.track.mute();
        }
    }

    getTrack(participantId, source) {
        const participant = this.room?.remoteParticipants.get(participantId);
        if (participant) {
            const publication = participant.getTrackPublication(source);
            return publication?.track;
        }
        return null;
    }

    async publishInfo(info) {
        log("Publishing info change:", info);
        const data = JSON.stringify({type: "info_change", info});
        const payload = new TextEncoder().encode(data);
        await this.room?.localParticipant.publishData(payload, {reliable: true});
        await this.setMicrophoneMuted(info.isSelfMuted);
    }

    async setMicrophoneMuted(muted) {
        log("Setting microphone mute to:", muted);
        const publication = this.room?.localParticipant.getTrackPublication(
            window.LivekitClient.Track.Source.Microphone
        );
        if (publication && publication.track.isMuted !== muted) {
            if (muted) {
                await publication.track.mute();
            } else {
                await publication.track.unmute();
            }
        }
    }

    async switchAudioInputDevice(deviceId) {
        log("Switching audio input device to:", deviceId);
        await this.room?.switchActiveDevice("audioinput", deviceId);
    }
}

export const livekitService = new LivekitService();

const Source = {
    CAMERA: window.LivekitClient.Track.Source.Camera,
    MICROPHONE: window.LivekitClient.Track.Source.Microphone,
    SCREEN: window.LivekitClient.Track.Source.ScreenShare,
};

console.log("Livekit Source constants:", Source);

Object.freeze(Source);

export {Source};
