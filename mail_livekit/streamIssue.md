Problem Summary: "Skipping incoming track as it already ended" The Error Receiver side
error: "skipping incoming track as it already ended"

Occurs when sender toggles camera on Appears in receiver's console, not sender's Video
feed breaks for receivers Root Cause Identified Odoo's behavior when toggling camera:

Camera OFF: Odoo calls updateUpload("camera", undefined) → triggers unpublish Camera ON:
Odoo calls updateUpload("camera", newTrack) → triggers publish with brand new
MediaStreamTrack (different ID) Odoo immediately stops the old track after creating the
new one (via setVideo() or closeStream()) The race condition:

LiveKit unpublishes old track → publishes new track (async operations) Meanwhile, Odoo
stops the MediaStreamTrack we're trying to publish Track ends before/during LiveKit's
publish operation Receivers attempt to subscribe to an already-ended track What We've
Tried (All Failed) Track cloning - Clone tracks immediately to prevent Odoo from
stopping them

Result: Clones still end somehow Delayed unpublish - Wait 500ms before unpublishing to
give receivers time

Result: Error persists Keep old clones alive - Don't stop old clones, accumulate them

Result: Error persists Use replaceTrack() - Avoid unpublish/publish cycle, keep same
publication

Current approach: Uses LiveKit's LocalTrack.replaceTrack() to swap underlying
MediaStreamTrack Result: Unknown (just implemented) Key Observations from Logs This
suggests: The track is alive when published on sender side, but ends between publish and
receiver subscription.

The Critical Question Why does the track end after successful publish?

Is Odoo stopping it even after we clone it? Is the clone somehow linked to the
original's lifecycle? Is LiveKit stopping it during internal operations? Is there a
timing issue with the WebRTC negotiation? Expected Behavior When sender toggles camera:

Old video publication should be replaced seamlessly Receivers should receive a live
track Video should continue without interruption
