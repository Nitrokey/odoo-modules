# Discuss LiveKit Integration (Odoo 18)

This addon integrates **LiveKit** as the media layer (audio/video/screen share) for
**Odoo Discuss calls**, while keeping Odoo’s **native call UI and semantics**.

It is designed to be safe to install even when LiveKit is not configured: when LiveKit
is disabled/misconfigured, Discuss falls back to the default Odoo RTC behavior.

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

- `discuss_livekit_integration.livekit_enabled` (boolean)
- `discuss_livekit_integration.livekit_server_url` (string)
- `discuss_livekit_integration.livekit_api_key` (string)
- `discuss_livekit_integration.livekit_api_secret` (string)

Frontend assets are conditionally loaded only when LiveKit is enabled and credentials
are present (see `views/livekit_assets_templates.xml`).

### Backend endpoints

- `POST /livekit/token` (JSON)
  - Issues a LiveKit JWT for a Discuss channel.
  - Works for authenticated users and guests/public pages.
- Presence/session endpoints (public + guest-aware):
  - `POST /mail/livekit/channel/join_call`
  - `POST /mail/livekit/channel/leave_call`
  - `POST /mail/livekit/session/update_and_broadcast`
  - `POST /discuss/livekit/channel/ping`

## Notes

- **Public channels / guests** are supported.
- **Only microphone selection is implemented** (parity with the existing Odoo call
  settings UI). Camera/speaker selection are intentionally not added.

## Vendor pinning / self-hosting

### Bundled vendor JS (recommended)

This repo includes a small bundling setup that produces a browser-ready vendor bundle:

- Output: `static/lib/bundles/livekit_vendor_entry.js`
- Build: `npm install` then `npm run bundle:livekit`

The addon asset bundle includes the generated vendor file, so production does not need
Node and does not need a CDN.

Practical options:

- Keep versions pinned and allowlist the CDN in your CSP.
- Replace the CDN URLs in the loader files with your own hosted URLs.
- If you upgrade LiveKit, upgrade both the client and processors together and test
  reconnect + screen share paths.

## Dev quickstart

From the workspace root (`/code`):

- Build: `./build`
- Start services: `docker-compose up -d`
- Enter container: `./bash`
- Run Odoo (install/update module): `./start -u discuss_livekit_integration`
