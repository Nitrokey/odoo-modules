/** @odoo-module */

/* global globalThis */

const LIVEKIT_VENDOR_BUNDLE_URL = "/discuss_livekit_integration/static/lib/bundles/livekit_vendor_entry.js";

function getLivekitClient() {
    // `browser.globalThis` is not defined in Odoo's browser service.
    // We attach ESM loader exports to the real global object.
    return globalThis.LivekitClient || window.LivekitClient;
}

function getLivekitTrackProcessors() {
    return globalThis.LivekitTrackProcessors || window.LivekitTrackProcessors;
}

/** @type {Map<string, Promise<void>>} */
const scriptPromises = new Map();

function loadScriptOnce(scriptUrl, {type} = {}) {
    if (scriptPromises.has(scriptUrl)) {
        return scriptPromises.get(scriptUrl);
    }
    const promise = new Promise((resolve, reject) => {
        const el = document.createElement("script");
        if (type) {
            el.type = type;
        }
        el.src = scriptUrl;
        el.async = true;
        el.addEventListener("load", () => resolve());
        el.addEventListener("error", () => reject(new Error(`Failed to load script: ${scriptUrl}`)));
        document.head.appendChild(el);
    });
    scriptPromises.set(scriptUrl, promise);
    return promise;
}

async function ensureSdkLoaded() {
    if (getLivekitClient()) {
        return;
    }

    await loadScriptOnce(LIVEKIT_VENDOR_BUNDLE_URL);
    if (getLivekitClient()) {
        return;
    }

    throw new Error("LiveKit SDK did not load");
}

async function ensureTrackProcessorsLoaded() {
    if (getLivekitTrackProcessors()) {
        return;
    }

    await ensureSdkLoaded();
    if (getLivekitTrackProcessors()) {
        return;
    }

    throw new Error("LiveKit track processors did not load");
}

export {getLivekitClient, getLivekitTrackProcessors, loadScriptOnce, ensureSdkLoaded, ensureTrackProcessorsLoaded};
