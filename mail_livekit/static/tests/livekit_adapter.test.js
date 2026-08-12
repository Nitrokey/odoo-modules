import {after, afterEach, describe, expect, test} from "@odoo/hoot";
import {Source, livekitService} from "@mail_livekit/discuss/livekit_service";
import {LiveKitAdapter} from "@mail_livekit/discuss/livekit_adapter";
import {cleanupLivekitService} from "./livekit_test_helpers";

const originalLivekitClient = window.LivekitClient;

function makeRemoteAudioTrack(identity) {
    const audioElement = document.createElement("audio");
    const track = {
        kind: "audio",
        attach: () => audioElement,
        detach: () => {
            // Detach the audio element
        },
    };
    const publication = {
        source: Source.MICROPHONE,
        track,
        isSubscribed: true,
    };
    const participant = {
        identity,
        sid: `${identity}-sid`,
        audioTrackPublications: new Map([["microphone", publication]]),
        videoTrackPublications: new Map(),
    };
    return {audioElement, participant, publication, track};
}

function makeRemoteAudioPublication(identity, {isSubscribed = false} = {}) {
    const publication = {
        source: Source.MICROPHONE,
        track: null,
        isSubscribed,
        setSubscribed: (subscribed) => {
            publication.requestedSubscription = subscribed;
        },
    };
    const participant = {
        identity,
        sid: `${identity}-sid`,
        audioTrackPublications: new Map([["microphone", publication]]),
        videoTrackPublications: new Map(),
    };
    return {participant, publication};
}

describe("mail_livekit livekit adapter", () => {
    after(() => {
        window.LivekitClient = originalLivekitClient;
    });

    afterEach(() => {
        cleanupLivekitService();
    });

    test("connect does not drop audio subscribed while the room connection is starting", async () => {
        const adapter = new LiveKitAdapter();
        const emittedPayloads = [];
        const {audioElement, participant, publication, track} =
            makeRemoteAudioTrack("partner:8");
        const originalConnect = livekitService.connect;

        livekitService.connect = async () => {
            livekitService.handleTrackSubscribed(track, publication, participant);
        };

        adapter.addEventListener("setAudioVolume", (event) => {
            emittedPayloads.push(event.detail.payload);
        });

        try {
            await adapter.connect("wss://livekit.example", "token");
        } finally {
            livekitService.connect = originalConnect;
        }

        expect(emittedPayloads).toEqual([
            {
                element: audioElement,
                identity: "partner:8",
            },
        ]);
    });

    test("rebindExistingTracks replays audio already subscribed during connection startup", async () => {
        const {audioElement, participant, track} = makeRemoteAudioTrack("partner:9");
        const subscribedTracks = [];

        livekitService.room = {
            remoteParticipants: new Map([[participant.identity, participant]]),
        };
        livekitService.connected = false;
        livekitService.subscribeToTrackSubscribed(
            "adapter",
            (identity, source, subscribedTrack, element) => {
                subscribedTracks.push({
                    element,
                    identity,
                    source,
                    track: subscribedTrack,
                });
            }
        );

        await livekitService.rebindExistingTracks();

        expect(subscribedTracks.length).toBe(1);
        expect(subscribedTracks[0]).toEqual({
            element: audioElement,
            identity: "partner:9",
            source: Source.MICROPHONE,
            track,
        });
    });

    test("rebindExistingTracks requests missing remote microphone subscriptions in a multi-person call", async () => {
        const {participant: alreadySubscribed} = makeRemoteAudioTrack("partner:10");
        const {participant: missingPeerA, publication: missingPublicationA} =
            makeRemoteAudioPublication("partner:11");
        const {participant: missingPeerB, publication: missingPublicationB} =
            makeRemoteAudioPublication("partner:12");

        livekitService.room = {
            remoteParticipants: new Map([
                [alreadySubscribed.identity, alreadySubscribed],
                [missingPeerA.identity, missingPeerA],
                [missingPeerB.identity, missingPeerB],
            ]),
        };

        await livekitService.rebindExistingTracks();

        expect(missingPublicationA.requestedSubscription).toBe(true);
        expect(missingPublicationB.requestedSubscription).toBe(true);
    });
});
