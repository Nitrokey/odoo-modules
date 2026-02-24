/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {Composer} from "@mail/core/common/composer";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {patch} from "@web/core/utils/patch";
import {toRaw} from "@odoo/owl";

const superSendMessage = Composer.prototype.sendMessage;

patch(Composer.prototype, {
    async sendMessage() {
        const composer = toRaw(this.props.composer);
        if (composer.message) {
            return superSendMessage.apply(this, arguments);
        }

        const thread = toRaw(composer.thread);
        const type = this.props.type; // 'message' or 'note'

        const externalRecipients = [];

        if (type !== "note" && thread && thread.model !== "discuss.channel") {
            const followers = thread.followers || [];
            for (const follower of followers) {
                const partner = toRaw(follower.partner);
                if (partner && !partner.isInternalUser) {
                    const name = partner.name || partner.email;
                    if (name && !externalRecipients.includes(name)) {
                        externalRecipients.push(name);
                    }
                }
            }
        }

        const mentionedPartners = composer.mentionedPartners || [];
        for (const partner of mentionedPartners) {
            if (!partner.isInternalUser) {
                const name = partner.name || partner.email;
                if (!externalRecipients.includes(name)) {
                    externalRecipients.push(name);
                }
            }
        }

        if (type !== "note" && thread && thread.suggestedRecipients) {
            for (const recipient of thread.suggestedRecipients) {
                if (recipient.checked && recipient.persona) {
                    const persona = this.store.Persona.get(recipient.persona);
                    if (persona && !persona.isInternalUser) {
                        const name = persona.name || persona.email || recipient.name;
                        if (name && !externalRecipients.includes(name)) {
                            externalRecipients.push(name);
                        }
                    }
                }
            }
        }

        if (externalRecipients.length > 0) {
            const recipientNames = externalRecipients.join(", ");
            const message = _t(
                "There are recipients that are not Odoo Internal Users: %(names)s. Are you sure you want to send this message?",
                {names: recipientNames}
            );

            return new Promise((resolve) => {
                this.env.services.dialog.add(ConfirmationDialog, {
                    title: _t("Send to external recipients?"),
                    body: message,
                    confirm: async () => {
                        await superSendMessage.apply(this, arguments);
                        resolve();
                    },
                    cancel: () => {
                        resolve();
                    },
                });
            });
        }

        return superSendMessage.apply(this, arguments);
    },
});
