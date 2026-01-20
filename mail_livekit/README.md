# Discuss LiveKit Integration (Odoo 18)

This addon integrates **LiveKit** as the WebRTC transport layer for **Odoo Discuss
calls**, replacing Odoo's built-in P2P and SFU connections while preserving the native
call UI and user experience.

## Architecture

### Core Components

The integration uses a layered architecture that bridges LiveKit's media handling with
Odoo's RTC semantics:

**LiveKit Service** (`livekit_service.js`)

- Singleton wrapper around LiveKit SDK Room API
- Manages connection lifecycle, track publishing, and event subscriptions
- Provides abstraction for camera, microphone, and screen share controls
- Handles LiveKit-specific events (TrackSubscribed, TrackMuted, etc.)

**LiveKit Adapter** (`livekit_adapter.js`)

- Translates between LiveKit events and Odoo's Network interface
- Emits Odoo-compatible events (`track`, `trackSubscribed`, `info_change`)
- Maps LiveKit Source types (CAMERA, MICROPHONE, SCREEN) to Odoo types (camera, audio,
  screen)
- Handles audio track special case (uses MediaStreamTrack for Odoo audio processing)

**RTC Patch** (`rtc_livekit_patch.js`)

- Patches Odoo's `Rtc` and `RtcSession` models to use LiveKit
- Replaces `_initConnection()` to instantiate LiveKitAdapter instead of P2P/SFU
- Disables P2P offer acceptance and SFU hot-swap handling
- Stores LiveKit tracks in separate Map (`session.livekitTracks`)
- Creates dummy MediaStream for UI rendering while actual video uses LiveKit tracks
- Implements event-driven track binding via `LIVEKIT:TRACK:REBIND` bus events

**Video Component Patch** (`call_participant_video_patch.js`)

- Patches `CallParticipantVideo` to handle LiveKit track attachment
- Overrides `_update()` to use LiveKit's `track.attach()` API directly
- Listens for `LIVEKIT:TRACK:REBIND` events to rebind tracks on changes
- Properly detaches tracks on component unmount to prevent memory leaks

### Track Lifecycle

**Video/Screen Tracks:**

1. LiveKit emits `TrackSubscribed` event with LiveKit Track object
2. Adapter forwards to RTC patch as `trackSubscribed` event
3. RTC patch stores track in `session.livekitTracks` Map
4. RTC patch creates dummy MediaStream in `session.videoStreams` (triggers UI rendering)
5. RTC patch fires `LIVEKIT:TRACK:REBIND` bus event
6. CallParticipantVideo receives event and calls `_update()`
7. `_update()` checks for LiveKit track and uses `track.attach(videoElement)` directly

**Audio Tracks:**

- Uses MediaStreamTrack extraction for compatibility with Odoo's audio processing
- Flows through standard Odoo RTC track handling

**Why Dummy MediaStream?**

- Odoo's UI checks `hasVideo` which requires `videoStream` existence
- LiveKit tracks must use `.attach()` API, not MediaStream `srcObject`
- Solution: dummy stream for rendering triggers, LiveKit track for actual video

## Configuration

### Settings UI

Configure in **Settings → LiveKit Integration**:

- Enable LiveKit
- LiveKit Server URL
- LiveKit API Key
- LiveKit API Secret

### `ir.config_parameter` keys

- `mail_livekit.livekit_enabled` (boolean)
- `mail_livekit.livekit_server_url` (string)
- `mail_livekit.livekit_api_key` (string)
- `mail_livekit.livekit_api_secret` (string)

## Implementation Notes

### Dual Storage Pattern

RtcSession maintains two track storage systems:

- `videoStreams` (Map): Dummy MediaStreams for UI rendering compatibility
- `livekitTracks` (Map): Actual LiveKit Track objects for video attachment

### Event Bus Pattern

Uses Odoo's `env.bus` for event propagation:

- `store.env.bus.trigger("LIVEKIT:TRACK:REBIND", {sessionId, type})`
- `useExternalListener(this.env.bus, "LIVEKIT:TRACK:REBIND", callback)`

This matches Odoo's existing patterns (e.g., `RTC-SERVICE:PLAY_MEDIA`)

### Bundled Livekit SDK 2.17

- Includes LiveKit client SDK and processors

## Limitations

- P2P connections are disabled when LiveKit is active
- SFU hot-swap is not applicable (LiveKit maintains single connection)
- Microphone device switching implemented; camera/speaker selection not added
