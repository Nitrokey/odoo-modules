/** @odoo-module */

import {Command, serverState} from "@web/../tests/web_test_helpers";
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
import {mockLivekit} from "./livekit_test_helpers";

describe.current.tags("desktop");
defineMailModels();

/**
 * Starts a call in a channel shared with "Zoe", who is already talking: the
 * `<audio>` element carrying her voice is returned.
 *
 * @param {Object} [param0]
 * @param {Number} [param0.savedVolume] volume saved for Zoe in the user settings
 */
async function startCallWithTalkingPeer({savedVolume} = {}) {
    mockGetMedia();
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({name: "Zoe"});
    const channelId = pyEnv["discuss.channel"].create({
        name: "General",
        channel_member_ids: [
            Command.create({partner_id: serverState.partnerId}),
            Command.create({partner_id: partnerId}),
        ],
    });
    const [memberId] = pyEnv["discuss.channel.member"].search([
        ["channel_id", "=", channelId],
        ["partner_id", "=", partnerId],
    ]);
    pyEnv["discuss.channel.rtc.session"].create({
        channel_member_id: memberId,
        channel_id: channelId,
    });
    if (savedVolume !== undefined) {
        pyEnv["res.users.settings.volumes"].create({
            user_setting_id: pyEnv["res.users.settings"].create({
                user_id: serverState.userId,
            }),
            partner_id: partnerId,
            volume: savedVolume,
        });
    }
    const livekit = mockLivekit({identity: `partner:${serverState.partnerId}`});
    await start();
    await openDiscuss(channelId);
    await click("[title='Start a Call']");
    await contains(".o-discuss-Call");
    await waitUntil(() => livekit.isConnected, {
        timeout: 2000,
        message: "the call should be connected to the LiveKit room",
    });
    livekit.addRemotePeer(`partner:${partnerId}`).startMicrophone();
    // The audio elements are appended to the document body, outside the test
    // fixture, so they are looked up by id rather than with `contains`.
    const audioElement = await waitUntil(
        () => document.getElementById(`livekit-audio-partner:${partnerId}`),
        {
            timeout: 2000,
            message: "the audio of the other attendee should be attached",
        }
    );
    // LiveKit attaches the element synchronously, but Odoo only takes ownership
    // of it a few ticks later. Applying a volume (the saved one, or the 0.5
    // default) is what marks the end of that handover.
    await waitUntil(() => audioElement.volume !== 1, {
        timeout: 2000,
        message: "Odoo should take ownership of the attached audio element",
    });
    return {audioElement, livekit, partnerId, pyEnv};
}

test("deafening mutes the audio received from the other attendees", async () => {
    const {audioElement} = await startCallWithTalkingPeer();
    expect(audioElement.muted).toBe(false);

    await click(".o-discuss-CallActionList button[aria-label='Deafen']");
    await contains(".o-discuss-CallActionList button[aria-label='Undeafen']");
    expect(audioElement.muted).toBe(true);

    await click(".o-discuss-CallActionList button[aria-label='Undeafen']");
    await contains(".o-discuss-CallActionList button[aria-label='Deafen']");
    expect(audioElement.muted).toBe(false);
});

test("the volume saved for an attendee is applied to the audio received", async () => {
    const {audioElement} = await startCallWithTalkingPeer({savedVolume: 0.31});
    expect(audioElement.volume).toBe(0.31);
});
