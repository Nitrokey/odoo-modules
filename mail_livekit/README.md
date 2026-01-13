# Discuss LiveKit Integration (Odoo 18)

This addon integrates **LiveKit** as the media layer (audio/video/screen share) for
**Odoo Discuss calls**, while keeping Odoo’s **native call UI and semantics**.

It is designed to be safe to install even when LiveKit is not configured. When livekit
has credentials and is enabled its assets will be added to the relevant pages. Upon
toggling livekit, it may be necessary to hard refresh the browser to ensure assets are
reloaded.

## What it does

- Replaces the underlying RTC media transport with **LiveKit Rooms**.
- Mirrors LiveKit participation into Odoo’s mail store as **synthetic RTC sessions**, so
  the standard Discuss call UI renders normally.

## Features

- **Audio + video + group calls** via LiveKit.
- **Screen sharing** bridged into the standard UI.
- **Background blur** using LiveKit track processors (applies immediately).
- **Microphone input selection** (uses Odoo’s existing “Input device” setting and
  hot-switches while in-call).
- **Multi-tab coordination** (host/follower model): only one tab publishes media for a
  channel.
- **Reconnection handling**: maps LiveKit connection states into the native UI and
  avoids excessive toasts.
- **Call invitations / ringing** semantics: triggers the stock incoming call UI/sound
  when a call starts in non-channel threads.

## Configuration

### Settings UI

Configure in **Settings → LiveKit Integration**:

- Enable LiveKit
- LiveKit Server URL
- LiveKit API Key
- LiveKit API Secret

### `ir.config_parameter` keys

This addon reads the following configuration parameters:

- `mail_livekit.livekit_enabled` (boolean)
- `mail_livekit.livekit_server_url` (string)
- `mail_livekit.livekit_api_key` (string)
- `mail_livekit.livekit_api_secret` (string)

## Notes

- **Public channels / guests** are supported.
- **Only microphone selection is implemented** (parity with the existing Odoo call
  settings UI). Camera/speaker selection are intentionally not added.

### Bundled vendor JS

This repo includes a small bundling setup that produces a browser-ready vendor bundle:

- Output: `static/lib/bundles/livekit_vendor_entry.js`
- Build: `npm install` then `npm run bundle:livekit`

- If you upgrade LiveKit, upgrade both the client and processors together and test
  reconnect + screen share paths.
