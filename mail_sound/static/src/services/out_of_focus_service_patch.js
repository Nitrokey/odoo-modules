// @odoo-module

import {OutOfFocusService} from "@mail/core/common/out_of_focus_service";
import {patch} from "@web/core/utils/patch";

/**
 * Patch the OutOfFocusService to always play notification sounds
 * regardless of browser focus state.
 *
 * This extends the standard notification behavior to play sounds
 * even when the browser window has focus, ensuring users never
 * miss notifications.
 */
patch(OutOfFocusService.prototype, {
    /**
     * Override notify to always play sound for incoming messages.
     *
     * @override
     * @param {Object} message - The message object
     */
    async notify(message) {
        // Call parent implementation to maintain standard notification behavior
        await super.notify(...arguments);
        const currentUser = this.env.services["mail.store"].self;
        const currentUserId = currentUser?.id;

        // Always play sound for messages from other users
        // The parent notify() already handles the focus-dependent behavior,
        // so we add unconditional sound playback here
        if (message && message.author && message.author.id !== currentUserId) {
            // Play the notification sound using the internal _playSound method
            // This ensures sound plays regardless of browser focus state
            this._playSound();
        }
    },
});
