import {Source, livekitService} from "@mail_livekit/discuss/livekit_service";
import {after} from "@odoo/hoot";
import {patchWithCleanup} from "@web/../tests/web_test_helpers";

export {Source};

/**
 * `livekitService` is a module level singleton: it survives from one test to
 * the next one. This resets every piece of state it keeps.
 */
export function cleanupLivekitService() {
    livekitService.infoChangeListeners.clear();
    livekitService.trackSubscribedListeners.clear();
    livekitService.trackMutedListeners.clear();
    livekitService.room = null;
    livekitService.connected = false;
    livekitService.initiated = false;
    document
        .querySelectorAll(`.${livekitService.audioElementClass}`)
        .forEach((element) => element.remove());
}

/**
 * Stand-in for a `LocalTrack`/`RemoteTrack` of the LiveKit SDK.
 */
export class MockLivekitTrack {
    constructor(kind, source, mediaStreamTrack = null) {
        this.kind = kind;
        this.source = source;
        this.mediaStreamTrack = mediaStreamTrack;
        this.isMuted = false;
        this.stopped = false;
        this.attachedElements = [];
    }

    attach(element) {
        const target =
            element ??
            document.createElement(this.kind === "audio" ? "audio" : "video");
        if (!this.attachedElements.includes(target)) {
            this.attachedElements.push(target);
        }
        return target;
    }

    detach(element) {
        if (element) {
            this.attachedElements = this.attachedElements.filter(
                (el) => el !== element
            );
            return element;
        }
        const detached = this.attachedElements;
        this.attachedElements = [];
        return detached;
    }

    async mute() {
        this.isMuted = true;
        if (this.mediaStreamTrack) {
            this.mediaStreamTrack.enabled = false;
        }
    }

    async unmute() {
        this.isMuted = false;
        if (this.mediaStreamTrack) {
            this.mediaStreamTrack.enabled = true;
        }
    }

    async replaceTrack(mediaStreamTrack) {
        this.mediaStreamTrack = mediaStreamTrack;
    }

    stop() {
        this.stopped = true;
    }
}

class MockLocalParticipant {
    constructor(identity) {
        this.identity = identity;
        this.sid = `${identity}-local-sid`;
        this.trackPublications = new Map();
        this.publishedData = [];
    }

    getTrackPublication(source) {
        return this.trackPublications.get(source);
    }

    async publishTrack(mediaStreamTrack, {source} = {}) {
        const publication = {
            source,
            isSubscribed: true,
            track: new MockLivekitTrack(
                mediaStreamTrack.kind,
                source,
                mediaStreamTrack
            ),
        };
        this.trackPublications.set(source, publication);
        return publication;
    }

    async unpublishTrack(track) {
        for (const [source, publication] of this.trackPublications) {
            if (publication.track === track) {
                this.trackPublications.delete(source);
            }
        }
    }

    async publishData(payload, options) {
        this.publishedData.push({payload, options});
    }
}

class MockRoom {
    constructor(identity, remoteParticipants) {
        this.localParticipant = new MockLocalParticipant(identity);
        // The other attendees outlive the local connection: they are still in
        // the room when the local session leaves and joins again.
        this.remoteParticipants = remoteParticipants;
        this.canPlaybackAudio = true;
        this.disconnectCount = 0;
    }

    async disconnect() {
        this.disconnectCount++;
    }

    async switchActiveDevice() {
        // Nothing to switch on a mocked room
    }
}

/**
 * A second (or third, ...) user of the call, seen from the browser session
 * under test: the tracks they publish are delivered through the very same
 * `livekitService` handlers the LiveKit SDK calls in production.
 */
export class RemoteLivekitPeer {
    constructor(identity, remoteParticipants) {
        this.identity = identity;
        this.sid = `${identity}-sid`;
        this.remoteParticipants = remoteParticipants;
        this.audioTrackPublications = new Map();
        this.videoTrackPublications = new Map();
        remoteParticipants.set(identity, this);
    }

    getTrackPublication(source) {
        return (
            this.audioTrackPublications.get(source) ??
            this.videoTrackPublications.get(source)
        );
    }

    _publications(source) {
        return source === Source.MICROPHONE
            ? this.audioTrackPublications
            : this.videoTrackPublications;
    }

    _publish(kind, source) {
        const track = new MockLivekitTrack(kind, source);
        const publication = {
            source,
            track,
            isSubscribed: true,
            setSubscribed: (subscribed) => {
                publication.requestedSubscription = subscribed;
            },
        };
        this._publications(source).set(source, publication);
        livekitService.handleTrackSubscribed(track, publication, this);
        return publication;
    }

    _unpublish(source) {
        const publications = this._publications(source);
        const publication = publications.get(source);
        if (!publication) {
            throw new Error(`${this.identity} has no published "${source}" track`);
        }
        publications.delete(source);
        livekitService.handleTrackUnsubscribed(publication.track, publication, this);
        return publication;
    }

    startScreenShare() {
        return this._publish("video", Source.SCREEN);
    }

    stopScreenShare() {
        return this._unpublish(Source.SCREEN);
    }

    startCamera() {
        return this._publish("video", Source.CAMERA);
    }

    stopCamera() {
        return this._unpublish(Source.CAMERA);
    }

    startMicrophone() {
        return this._publish("audio", Source.MICROPHONE);
    }

    /** The peer leaves the LiveKit room (hangs up, closes the tab, crashes, ...). */
    leave() {
        this.remoteParticipants.delete(this.identity);
        livekitService.handleParticpantDisconnected(this);
    }
}

/**
 * Replaces the connection to a real LiveKit SFU by an in-memory room, so that a
 * test can drive what the other participants of the call do. Everything else of
 * `livekitService` (track (un)subscription, mute handling, disconnection,
 * audio element bookkeeping) keeps running for real.
 *
 * @param {Object} [param0]
 * @param {String} [param0.identity] LiveKit identity of the browser session under test.
 */
export function mockLivekit({identity = "local"} = {}) {
    const state = {
        connectCount: 0,
        disconnectCount: 0,
        remoteParticipants: new Map(),
        room: null,
    };
    patchWithCleanup(livekitService, {
        async connect() {
            state.connectCount++;
            state.room = new MockRoom(identity, state.remoteParticipants);
            this.room = state.room;
            this.connected = true;
            this.initiated = false;
            // Joining a room delivers what the attendees already publish, which
            // the service handles on `RoomEvent.Connected`.
            await this.rebindExistingTracks();
        },
        async disconnect() {
            state.disconnectCount++;
            return super.disconnect(...arguments);
        },
    });
    after(cleanupLivekitService);
    return {
        get room() {
            return state.room;
        },
        get connectCount() {
            return state.connectCount;
        },
        get disconnectCount() {
            return state.disconnectCount;
        },
        get isConnected() {
            return livekitService.connected;
        },
        /** The microphone publication of the browser session under test, if any. */
        get microphonePublication() {
            return state.room?.localParticipant.getTrackPublication(Source.MICROPHONE);
        },
        /**
         * @param {String} peerIdentity e.g. `partner:7`
         * @returns {RemoteLivekitPeer}
         */
        addRemotePeer(peerIdentity) {
            if (!state.room) {
                throw new Error(
                    "cannot add a remote peer before the local session joined the room"
                );
            }
            return new RemoteLivekitPeer(peerIdentity, state.remoteParticipants);
        },
    };
}
