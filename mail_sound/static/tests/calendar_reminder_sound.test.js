import {defineCalendarModels} from "@calendar/../tests/calendar_test_helpers";
import {
    assertSteps,
    contains,
    start,
    startServer,
    step,
} from "@mail/../tests/mail_test_helpers";
import {describe, test} from "@odoo/hoot";
import {patchWithCleanup, serverState} from "@web/../tests/web_test_helpers";

describe.current.tags("desktop");
defineCalendarModels();

/**
 * Boots the webclient with the sounds of the notification service stepped
 * instead of played.
 */
async function startWithSteppedSounds() {
    const pyEnv = await startServer();
    const env = await start();
    patchWithCleanup(env.services["mail.sound_effects"], {
        play(soundEffectName) {
            step(soundEffectName);
        },
    });
    return {env, pyEnv};
}

function sendReminder(pyEnv) {
    pyEnv["bus.bus"]._sendone(serverState.partnerId, "calendar.alarm", [
        {
            alarm_id: 1,
            event_id: 2,
            title: "Meeting",
            message: "Very old meeting message",
            timer: 0,
            notify_at: "1978-04-14 12:45:00",
        },
    ]);
}

test("plays a sound along with a meeting reminder", async () => {
    const {pyEnv} = await startWithSteppedSounds();
    sendReminder(pyEnv);
    await contains(".o_notification", {text: "Very old meeting message"});
    assertSteps(["calendar-reminder"]);
});

test("plays the sound once per reminder", async () => {
    const {pyEnv} = await startWithSteppedSounds();
    sendReminder(pyEnv);
    await contains(".o_notification", {text: "Very old meeting message"});
    // The same alarm pushed again is already displayed, hence ignored.
    sendReminder(pyEnv);
    await contains(".o_notification", {count: 1});
    assertSteps(["calendar-reminder"]);
});

test("leaves the other notifications of the backend silent", async () => {
    const {env} = await startWithSteppedSounds();
    env.services.notification.add("Some unrelated notification");
    await contains(".o_notification", {text: "Some unrelated notification"});
    assertSteps([]);
});
