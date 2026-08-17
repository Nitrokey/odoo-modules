import {Command, serverState} from "@web/../tests/web_test_helpers";
import {Source, mockLivekit} from "./livekit_test_helpers";
import {
    click,
    contains,
    defineMailModels,
    mockGetMedia,
    openDiscuss,
    start,
    startServer,
} from "@mail/../tests/mail_test_helpers";
import {describe, expect, test, waitUntil} from "@odoo/hoot";
import {livekitService} from "@mail_livekit/discuss/livekit_service";
import {mailDataHelpers} from "@mail/../tests/mock_server/mail_mock_server";

describe.current.tags("desktop");
defineMailModels();

/**
 * Makes the partner `partnerId` ring the browser session under test on
 * `channelId`, the same way the server does when someone starts a call in a
 * channel we are a member of.
 */
function ringIncomingCall(pyEnv, {channelId, partnerId}) {
    const [memberId] = pyEnv["discuss.channel.member"].search([
        ["channel_id", "=", channelId],
        ["partner_id", "=", partnerId],
    ]);
    const sessionId = pyEnv["discuss.channel.rtc.session"].create({
        channel_member_id: memberId,
        channel_id: channelId,
    });
    const [self] = pyEnv["res.partner"].read(serverState.partnerId);
    pyEnv["bus.bus"]._sendone(
        self,
        "mail.record/insert",
        new mailDataHelpers.Store(
            pyEnv["discuss.channel.rtc.session"].browse(sessionId),
            {channelMember: {id: memberId}}
        )
            .add(pyEnv["discuss.channel.member"].browse(memberId), {
                persona: {id: partnerId, type: "partner"},
                thread: {id: channelId, model: "discuss.channel"},
            })
            .add(pyEnv["discuss.channel"].browse(channelId), {
                rtcInvitingSession: {id: sessionId},
            })
            .get_result()
    );
}

test("a voice-only call starts unmuted and mute changes reach the room", async () => {
    mockGetMedia();
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({name: "Bob"});
    const channelId = pyEnv["discuss.channel"].create({
        name: "Bob",
        channel_member_ids: [
            Command.create({partner_id: serverState.partnerId}),
            Command.create({partner_id: partnerId}),
        ],
    });
    const livekit = mockLivekit({identity: `partner:${serverState.partnerId}`});
    await start();
    ringIncomingCall(pyEnv, {channelId, partnerId});
    await contains(".o-discuss-CallInvitation");
    // Voice-only: accepted without the camera.
    await click(".o-discuss-CallInvitation [title='Accept']");
    await contains(".o-discuss-Call");
    // The receiver is not muted: the action offered is "Mute", not "Unmute".
    await contains(".o-discuss-CallActionList button[aria-label='Mute']");
    // ... and the microphone is published to the room, unmuted.
    await waitUntil(() => livekit.microphonePublication, {
        timeout: 2000,
        message: "the microphone should be published to the LiveKit room",
    });
    const publication = livekit.microphonePublication;
    expect(publication.track.isMuted).toBe(false);

    // Muting from Odoo reaches the publication the other attendees receive...
    await click(".o-discuss-CallActionList button[aria-label='Mute']");
    await contains(".o-discuss-CallActionList button[aria-label='Unmute']");
    await waitUntil(() => publication.track.isMuted, {
        timeout: 2000,
        message: "muting should mute the microphone published to the room",
    });

    // ... and so does unmuting.
    await click(".o-discuss-CallActionList button[aria-label='Unmute']");
    await contains(".o-discuss-CallActionList button[aria-label='Mute']");
    await waitUntil(() => !publication.track.isMuted, {
        timeout: 2000,
        message: "unmuting should unmute the microphone published to the room",
    });
});

test("setMicrophoneMuted unmutes the microphone published to the room", async () => {
    const livekit = mockLivekit();
    await livekitService.connect("wss://livekit.example", "token");
    // Publish a microphone track, then mute it (as Odoo does when joining).
    await livekitService.setTrackEnabled(Source.MICROPHONE, true, {
        kind: "audio",
        enabled: false,
    });
    const publication = livekit.microphonePublication;
    await publication.track.mute();
    expect(publication.track.isMuted).toBe(true);

    // Unmuting from Odoo must reach the LiveKit publication.
    await livekitService.setMicrophoneMuted(false);

    expect(publication.track.isMuted).toBe(false);
});

test("refusing a second incoming call keeps the ongoing call connected", async () => {
    mockGetMedia();
    const pyEnv = await startServer();
    const bobId = pyEnv["res.partner"].create({name: "Bob"});
    const carolId = pyEnv["res.partner"].create({name: "Carol"});
    const conferenceId = pyEnv["discuss.channel"].create({
        name: "Conference",
        channel_member_ids: [
            Command.create({partner_id: serverState.partnerId}),
            Command.create({partner_id: bobId}),
        ],
    });
    const directId = pyEnv["discuss.channel"].create({
        name: "Carol",
        channel_member_ids: [
            Command.create({partner_id: serverState.partnerId}),
            Command.create({partner_id: carolId}),
        ],
    });
    const [bobMemberId] = pyEnv["discuss.channel.member"].search([
        ["channel_id", "=", conferenceId],
        ["partner_id", "=", bobId],
    ]);
    pyEnv["discuss.channel.rtc.session"].create({
        channel_member_id: bobMemberId,
        channel_id: conferenceId,
    });
    const livekit = mockLivekit({identity: `partner:${serverState.partnerId}`});
    await start();
    await openDiscuss(conferenceId);
    await click("[title='Start a Call']");
    await contains(".o-discuss-Call");
    await waitUntil(() => livekit.isConnected, {
        timeout: 2000,
        message: "the conference should be connected to the LiveKit room",
    });
    const disconnectsBeforeRefusal = livekit.disconnectCount;

    // Carol calls directly while the conference is ongoing, and we refuse.
    ringIncomingCall(pyEnv, {channelId: directId, partnerId: carolId});
    await contains(".o-discuss-CallInvitation");
    await click(".o-discuss-CallInvitation [title='Refuse']");
    await contains(".o-discuss-CallInvitation", {count: 0});

    // Refusing Carol must leave the conference untouched.
    await contains(".o-discuss-Call");
    expect(livekit.disconnectCount).toBe(disconnectsBeforeRefusal);
    expect(livekit.isConnected).toBe(true);
});
