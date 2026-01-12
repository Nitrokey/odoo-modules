/** @odoo-module */

import {HOST_PING_INTERVAL_MS, HOST_PROBE_TIMEOUT_MS, LIVEKIT_BC_NAME, LIVEKIT_HOST_MSG, LIVEKIT_PROBE_MSG} from "./livekit_utils";

/**
 * Cross-tab coordination for LiveKit calls (host election + takeover).
 */
export class LivekitCrossTabCoordinator {
    constructor(state, warn) {
        this.state = state;
        this.warn = warn;
        this.eventListeners = {};
        this.broadcastChannel = null;
        this.hostPingInterval = null;
        this.lastHostPingTime = 0;
    }

    on(eventName, handler) {
        if (!this.eventListeners[eventName]) {
            this.eventListeners[eventName] = [];
        }
        this.eventListeners[eventName].push(handler);
    }

    emit(eventName, data) {
        const listeners = this.eventListeners[eventName] || [];
        for (const listener of listeners) {
            try {
                listener(data);
            } catch (e) {
                this.warn(`Error in ${eventName} listener:`, e);
            }
        }
    }

    initBroadcastChannel() {
        if (typeof BroadcastChannel === "undefined") {
            this.warn("BroadcastChannel not supported; multi-tab coordination disabled");
            return;
        }
        if (this.broadcastChannel) {
            return;
        }
        this.broadcastChannel = new BroadcastChannel(LIVEKIT_BC_NAME);
        this.broadcastChannel.onmessage = (event) => {
            const msg = event.data;
            if (!msg?.type) {
                return;
            }
            this.handleBroadcastMessage(msg);
        };
    }

    postBroadcast(msg) {
        if (!this.broadcastChannel) {
            return;
        }
        try {
            this.broadcastChannel.postMessage(msg);
        } catch (e) {
            this.warn("BroadcastChannel postMessage failed", e);
        }
    }

    postHostClose(channelId, reason) {
        this.postBroadcast({
            type: LIVEKIT_HOST_MSG.CLOSE,
            channelId,
            reason,
        });
    }

    stopHostPing() {
        if (this.hostPingInterval) {
            clearInterval(this.hostPingInterval);
            this.hostPingInterval = null;
        }
    }

    startHostPing() {
        this.stopHostPing();
        this.hostPingInterval = setInterval(() => {
            if (!this.state.isHost) {
                this.stopHostPing();
                return;
            }
            this.postBroadcast({
                type: LIVEKIT_HOST_MSG.PING,
                channelId: this.state.hostedChannelId,
            });
        }, HOST_PING_INTERVAL_MS);
    }

    sendHostSnapshot() {
        this.postBroadcast({
            type: LIVEKIT_HOST_MSG.INIT,
            channelId: this.state.hostedChannelId,
        });
    }

    /**
     * Probe for an active host tab.
     * @param {Number|String} channelId
     * @param {Number} timeoutMs
     * @returns {Promise<Boolean>}
     */
    async probeForActiveHost(channelId, timeoutMs = HOST_PROBE_TIMEOUT_MS) {
        return new Promise((resolve) => {
            const probeStartTime = Date.now();
            this.postBroadcast({
                type: LIVEKIT_PROBE_MSG,
                channelId,
            });
            setTimeout(() => {
                const hostActive = this.lastHostPingTime > probeStartTime;
                resolve(hostActive);
            }, timeoutMs);
        });
    }

    handleBroadcastMessage(msg) {
        const type = msg.type;

        if (type === LIVEKIT_HOST_MSG.INIT) {
            this.handleHostInit(msg);
        } else if (type === LIVEKIT_HOST_MSG.PING) {
            this.handleHostPing(msg);
        } else if (type === LIVEKIT_HOST_MSG.CLOSE) {
            this.handleHostClose(msg);
        } else if (type === LIVEKIT_PROBE_MSG) {
            this.handleProbe(msg);
        }
    }

    handleHostInit(msg) {
        if (this.state.isHost && msg.channelId === this.state.hostedChannelId) {
            this.warn("Host conflict detected; deferring to newer host", {
                channelId: msg.channelId,
            });
            this.emit("hostConflict", msg);
        }
        this.lastHostPingTime = Date.now();
    }

    handleHostPing() {
        this.lastHostPingTime = Date.now();
    }

    handleHostClose(msg) {
        if (this.state.isHost && msg.channelId === this.state.hostedChannelId) {
            this.warn("Another tab taking over; disconnecting this host", {
                channelId: msg.channelId,
                reason: msg.reason,
            });
            this.emit("hostTakeover", msg);
        }
    }

    handleProbe(msg) {
        if (this.state.isHost && msg.channelId === this.state.hostedChannelId) {
            this.sendHostSnapshot();
        }
    }

    destroy() {
        this.stopHostPing();
        if (this.broadcastChannel) {
            this.broadcastChannel.close();
            this.broadcastChannel = null;
        }
    }
}
