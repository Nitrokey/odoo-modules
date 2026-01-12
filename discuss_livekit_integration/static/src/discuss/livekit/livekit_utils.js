/** @odoo-module */

/**
 * Parse LiveKit participant identity string into Odoo persona type and ID.
 * @param {String} identity - LiveKit identity in format "partner_123" or "guest_456"
 * @returns {Object} Parsed identity object with optional partnerId or guestId
 */
export function parseLivekitIdentity(identity) {
    if (typeof identity !== "string") {
        return {};
    }
    if (identity.startsWith("partner_")) {
        const partnerId = Number(identity.slice("partner_".length));
        return Number.isFinite(partnerId) ? {partnerId} : {};
    }
    if (identity.startsWith("guest_")) {
        const guestId = Number(identity.slice("guest_".length));
        return Number.isFinite(guestId) ? {guestId} : {};
    }
    return {};
}

export const LIVEKIT_BC_NAME = "discuss.livekit.cross_tab";

export const LIVEKIT_HOST_MSG = {
    INIT: "INIT_HOST",
    PING: "PING_HOST",
    CLOSE: "CLOSE_HOST",
};

export const LIVEKIT_PROBE_MSG = "PROBE_HOST";

export const HEARTBEAT_INTERVAL_MS = 30000;
export const HOST_PING_INTERVAL_MS = 5000;
export const HOST_PROBE_TIMEOUT_MS = 1000;
export const HOST_TAKEOVER_DELAY_MS = 100;

export const CAMERA_CONFIG = {
    width: 1280,
};

export const BLUR_PROCESSOR_MAX_FPS = 24;

export const SESSION_INACTIVE_TIMEOUT_MS = 75000;
