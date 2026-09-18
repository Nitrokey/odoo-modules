// @odoo-module

import {calendarNotificationService} from "@calendar/js/services/calendar_notification_service";
import {patch} from "@web/core/utils/patch";

/**
 * Patch the calendar notification service to play a sound along with the
 * reminder of a meeting.
 *
 * The service builds its reminders inside its own closure, so there is no
 * method to override at the moment the notification is displayed. Wrap the
 * notification service it receives instead: only the reminders go through that
 * copy, every other notification of the backend stays silent.
 */
patch(calendarNotificationService, {
    dependencies: [...calendarNotificationService.dependencies, "mail.sound_effects"],

    start(env, services) {
        const {notification} = services;
        const soundEffects = services["mail.sound_effects"];
        soundEffects.soundEffects["calendar-reminder"] ??= {
            path: "/mail/static/src/audio/ting",
        };
        return super.start(env, {
            ...services,
            notification: {
                ...notification,
                add(message, options) {
                    soundEffects.play("calendar-reminder");
                    return notification.add(message, options);
                },
            },
        });
    },
});
