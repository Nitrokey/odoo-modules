/** @odoo-module */

const {Room, VideoPresets, RoomEvent} = window.LivekitClient;

// This script should be the only contact point with Livekit SDK

const Source = {
    CAMERA: window.LivekitClient.Track.Source.Camera,
    MICROPHONE: window.LivekitClient.Track.Source.Microphone,
    SCREEN: window.LivekitClient.Track.Source.ScreenShare,
};

Object.freeze(Source);

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

    _formAudioElementId(identity) {
        return `livekit-audio-${identity}`;
    }

    get audioElementClass() {
        return "livekit-audio-element";
    }

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
        if (
            this.room?.localParticipant &&
            participant.sid === this.room.localParticipant.sid
        ) {
            log("Ignoring own track subscription");
            return;
        }

        log("Track subscribed", track, publication, participant);

        let audioElement = null;

        if (track.kind == "audio") {
            const audioElementId = this._formAudioElementId(participant.identity);
            audioElement = document.getElementById(audioElementId);
            audioElement?.remove();

            audioElement = track.attach();
            audioElement.id = audioElementId;
            audioElement.classList.add(this.audioElementClass);
            document.body.appendChild(audioElement);
        }

        for (const listener of this.trackSubscribedListeners.values()) {
            listener(participant.identity, publication.source, track, audioElement);
        }
    }

    handleTrackUnsubscribed(track, publication, participant) {
        log("Track unsubscribed", track, publication, participant);
        track.detach();

        if (track.kind === "audio") {
            const audioElementId = this._formAudioElementId(participant.identity);
            const audioElement = document.getElementById(audioElementId);
            audioElement?.remove();
        }

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
        this.connected = false;
    }

    handleParticpantDisconnected(participant) {
        log("Participant disconnected", participant.identity);

        const audioElementId = this._formAudioElementId(participant.identity);
        const audioElement = document.getElementById(audioElementId);
        audioElement?.remove();
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

    // Add this method to the LivekitService class
    async rebindExistingTracks() {
        if (!this.room) {
            log("Cannot rebind - no LiveKit room");
            return;
        }

        log("Rebinding existing participant tracks");

        for (const [identity, participant] of this.room.remoteParticipants.entries()) {
            log(`Processing existing participant: ${identity}`);

            // Process audio tracks
            const audioTracks = Array.from(participant.audioTrackPublications.values());
            for (const publication of audioTracks) {
                if (publication.track && publication.isSubscribed) {
                    log(`Rebinding existing audio track for ${identity}`);
                    this.handleTrackSubscribed(
                        publication.track,
                        publication,
                        participant
                    );
                }
            }

            // Process video tracks
            const videoTracks = Array.from(participant.videoTrackPublications.values());
            for (const publication of videoTracks) {
                if (publication.track && publication.isSubscribed) {
                    log(`Rebinding existing video track for ${identity}`);
                    this.handleTrackSubscribed(
                        publication.track,
                        publication,
                        participant
                    );
                }
            }
        }
    }

    async connect(url, token) {
        if (this.initiated) {
            log("Already connected or connecting to LiveKit");
            return;
        }

        // If there's an existing room, disconnect it WITHOUT clearing listeners
        if (this.room) {
            log("Disconnecting existing room before reconnecting");
            const roomToDisconnect = this.room;
            this.room = null;
            this.connected = false;
            await roomToDisconnect.disconnect();
            // Note: We don't clear listeners or set initiated=false here
            // because we're reconnecting
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
            disconnectOnPageLeave: false,
        });

        await this.room.prepareConnection(url, token);

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
                    log("Issue with audio playback: requires UI interaction");
                }
            })
            .on(RoomEvent.Connected, () => {
                log("Room connected - rebinding existing tracks");
                setTimeout(() => this.rebindExistingTracks(), 100);
            })
            .on(RoomEvent.ParticipantDisconnected, (remoteParticipant) => {
                this.handleParticpantDisconnected(remoteParticipant);
            });

        try {
            await this.room.connect(url, token);
            log("Connected to LiveKit room");
            this.connected = true;
            this.initiated = false;
        } catch (error) {
            log("Failed to connect to LiveKit room:", error);
            this.room = null;
            this.initiated = false;
            this.connected = false;
            throw error;
        }
    }

    async disconnect() {
        if (!this.room && !this.initiated) {
            log("Already disconnected");
            return;
        }

        log("Disconnecting from LiveKit");

        // Unpublish and stop all local tracks before disconnecting
        if (this.room?.localParticipant) {
            log("Unpublishing all local tracks");
            const localTracks = Array.from(
                this.room.localParticipant.trackPublications.values()
            );

            for (const publication of localTracks) {
                if (publication.track) {
                    log("Stopping and unpublishing track:", publication.source);
                    try {
                        // Stop the track first
                        publication.track.stop();
                        // Then unpublish it
                        await this.room.localParticipant.unpublishTrack(
                            publication.track
                        );
                    } catch (e) {
                        log("Error unpublishing track:", e);
                    }
                }
            }
        }

        log("Clearing info change listeners");
        this.infoChangeListeners.clear();
        this.trackSubscribedListeners.clear();
        this.trackMutedListeners.clear();

        log("Removing all audio elements");
        const allLivekitAudio = document.querySelectorAll(".livekit-audio-element");
        allLivekitAudio.forEach((element) => {
            log("Removing orphaned audio element:", element.id);
            element.remove();
        });

        const roomToDisconnect = this.room;
        this.room = null;
        this.initiated = false;
        this.connected = false;

        if (roomToDisconnect) {
            await roomToDisconnect.disconnect();
        }
    }

    async setTrackEnabled(source, enabled, mediaStreamTrack = null) {
        log("Setting track enabled:", source, enabled, this.room);
        if (!this.room?.localParticipant) {
            log("Cannot set track - no local participant");
            return;
        }
        const publication = this.room?.localParticipant.getTrackPublication(source);

        if (mediaStreamTrack && enabled) {
            await this._publishOrReplaceTrack(source, publication, mediaStreamTrack);
        } else if (!enabled && publication?.track) {
            log("Muting/unmuting existing track for source:", source);
            await publication.track.mute();
        }
    }

    async _publishOrReplaceTrack(source, publication, mediaStreamTrack) {
        if (!publication) {
            log("Publishing new track for source:", source);
            await this.room?.localParticipant.publishTrack(mediaStreamTrack, {
                source,
                simulcast: source !== Source.Microphone,
            });
        } else if (publication.track) {
            log("Replacing track for source:", source);
            await publication.track.replaceTrack(mediaStreamTrack);
            if (
                publication.track.source !== Source.Microphone ||
                mediaStreamTrack?.enabled
            ) {
                publication?.track?.unmute();
            }
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
        try {
            const data = JSON.stringify({type: "info_change", info});
            const payload = new TextEncoder().encode(data);
            await this.room?.localParticipant.publishData(payload, {reliable: true});
            await this.setMicrophoneMuted(info.isSelfMuted);
        } catch (error) {
            log("Error publishing info:", error);
        }
    }

    async setMicrophoneMuted(muted) {
        log("Setting microphone mute to:", muted);
        const publication = this.room?.localParticipant.getTrackPublication(
            Source.Microphone
        );
        if (publication?.track && publication.track.isMuted !== muted) {
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

export {Source};
