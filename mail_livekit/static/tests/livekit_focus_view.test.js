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
import {describe, queryAll, test, waitUntil} from "@odoo/hoot";
import {mockLivekit} from "./livekit_test_helpers";

describe.current.tags("desktop");
defineMailModels();

/**
 * Cards of the call grid. In tile view it holds one card per participant (plus
 * one extra card per shared screen); in focus view it holds exactly one card,
 * the focused one (the small "inset" card is rendered outside of the grid).
 */
const MAIN_CARD = ".o-discuss-Call-mainCards .o-discuss-CallParticipantCard";

/**
 * Starts a call in a channel shared with a second user, and returns a handle on
 * that user as seen from the LiveKit room of the browser session under test.
 *
 * The peer is named "Zoe" so that they are sorted after "Mitchell Admin"
 * (cards are sorted by participant name).
 */
async function startCallWithPeer() {
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
    const livekit = mockLivekit({identity: `partner:${serverState.partnerId}`});
    await start();
    await openDiscuss(channelId);
    await click("[title='Start a Call']");
    await contains(".o-discuss-Call");
    // Tile view: one card for each of the two participants.
    await contains(MAIN_CARD, {count: 2});
    await waitUntil(() => livekit.isConnected, {
        timeout: 2000,
        message: "the call should be connected to the LiveKit room",
    });
    return {
        channelId,
        livekit,
        partnerId,
        peer: livekit.addRemotePeer(`partner:${partnerId}`),
        pyEnv,
    };
}

/**
 * Makes sure the call is in focus view on the only card showing a video. Once
 * a remote screen share puts the other attendees in focus view on its own, this
 * becomes a no-op.
 */
async function focusVideoCard() {
    if (queryAll(MAIN_CARD).length > 1) {
        await click(`${MAIN_CARD}:has(video)`);
    }
    await contains(MAIN_CARD, {count: 1});
}

test("a remote screen share puts the other attendees in focus view", async () => {
    const {peer} = await startCallWithPeer();
    peer.startScreenShare();
    // The shared screen is received...
    await contains(`${MAIN_CARD} video`);
    // ... and displayed alone, in focus view.
    await contains(MAIN_CARD, {count: 1});
});

test("focus view falls back to tile view when the focused screen share stops", async () => {
    const {peer} = await startCallWithPeer();
    peer.startScreenShare();
    await contains(`${MAIN_CARD} video`);
    await focusVideoCard();
    peer.stopScreenShare();
    // The screen is gone: staying in focus view would only show an empty tile.
    await contains(MAIN_CARD, {count: 2});
});

test("focus view falls back to tile view when a screen share stops with the camera on", async () => {
    const {peer} = await startCallWithPeer();
    // The camera alone does not focus anything, the screen share that follows does.
    peer.startCamera();
    peer.startScreenShare();
    await contains(`${MAIN_CARD} video`);
    await focusVideoCard();
    peer.stopScreenShare();
    // Back to the tiles, not to the sharer's camera in focus view.
    await contains(MAIN_CARD, {count: 2});
});

test("focus view falls back to tile view when the focused participant leaves", async () => {
    const {peer} = await startCallWithPeer();
    peer.startCamera();
    await contains(`${MAIN_CARD} video`);
    await focusVideoCard();
    // Zoe leaves the LiveKit room (hangs up, closes the tab, loses connection).
    peer.leave();
    // Her video is gone: staying in focus view would only show an empty tile.
    await contains(MAIN_CARD, {count: 2});
});
