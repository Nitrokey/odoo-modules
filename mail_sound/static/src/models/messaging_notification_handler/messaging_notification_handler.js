/** @odoo-module **/

import {registerInstancePatchModel} from "@mail/model/model_core";

registerInstancePatchModel(
  "mail.messaging_notification_handler",
  "mail_sound/static/src/models/messaging_notification_handler/messaging_notification_handler.js",
  {
    /**
     * Override to add sound playback for all chat messages
     * Plays sound regardless of browser focus state
     *
     * @override
     * @private
     */
    async _handleNotificationChannelMessage({id, message: messageData}) {
      // Call parent implementation
      await this._super({id, message: messageData});

      // Get the inserted message
      const message = this.messaging.models["mail.message"].findFromIdentifyingData({
        id: messageData.id,
      });

      // Play sound only if message exists and author is not current user
      if (
        message &&
        message.author !== this.messaging.currentPartner &&
        this.messaging &&
        this.messaging.soundEffects &&
        this.messaging.soundEffects.pushToTalk
      ) {
        this.messaging.soundEffects.pushToTalk.play();
      }
    },

    /**
     * Override to add sound playback for inbox/activity notifications
     * Plays sound when inbox notification arrives
     *
     * @override
     * @private
     */
    _handleNotificationNeedaction(data) {
      // Call parent implementation to update counters
      this._super(data);

      // Play notification sound
      if (
        this.messaging &&
        this.messaging.soundEffects &&
        this.messaging.soundEffects.pushToTalk
      ) {
        this.messaging.soundEffects.pushToTalk.play();
      }
    },
  }
);
