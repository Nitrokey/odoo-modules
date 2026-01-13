// Bundled vendor entrypoint.
// Produces a single IIFE bundle that exposes the dependencies on globalThis.

/* global globalThis */

import * as LivekitClient from "livekit-client";
import * as LivekitTrackProcessors from "@livekit/track-processors";

// Keep the same global contract used by the existing code.
globalThis.LivekitClient = LivekitClient;
globalThis.LivekitTrackProcessors = LivekitTrackProcessors;
