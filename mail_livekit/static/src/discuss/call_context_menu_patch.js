// Create new file: mail_livekit/static/src/discuss/call/common/call_context_menu_patch.js

import {CallContextMenu} from "@mail/discuss/call/common/call_context_menu";
import {patch} from "@web/core/utils/patch";

patch(CallContextMenu.prototype, {
    onChangeVolume(ev) {
        super.onChangeVolume(ev);

        // Immediately apply volume to LiveKit audio element
        const volume = Number(ev.target.value);
        const identity = this.props.rtcSession.partnerId
            ? `partner:${this.props.rtcSession.partnerId}`
            : `guest:${this.props.rtcSession.channelMember.id}`;
        const audioElementId = `livekit-audio-${identity}`;
        const audioElement = document.getElementById(audioElementId);

        if (audioElement) {
            audioElement.volume = volume;
        }
    },
});
