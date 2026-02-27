/** @odoo-module **/

import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";

const widget = registry.category("view_widgets").get("mail_composer_send_dropdown");
const MailComposerSendDropdown = widget?.component;

if (MailComposerSendDropdown) {
    const superOnClickSend = MailComposerSendDropdown.prototype.onClickSend;

    patch(MailComposerSendDropdown.prototype, {
        async onClickSend() {
            try {
                const externalRecipients =
                    await this._getExternalRecipientsForDropdown();
                if (externalRecipients.length > 0) {
                    const names = externalRecipients.join(", ");
                    const body = _t(
                        "There are recipients that are not Odoo Internal Users: %(names)s. Are you sure you want to send this message?",
                        {names}
                    );

                    return new Promise((resolve) => {
                        this.dialogService.add(ConfirmationDialog, {
                            title: _t("Send to external recipients?"),
                            body,
                            confirm: async () => {
                                await superOnClickSend.apply(this, arguments);
                                resolve();
                            },
                            cancel: () => resolve(),
                        });
                    });
                }
            } catch (e) {
                console.error("mail_confirm_external_recipient (full composer)", e);
            }

            return superOnClickSend.apply(this, arguments);
        },

        async _getExternalRecipientsForDropdown() {
            const mailStore = this.env.services["mail.store"];
            const {Thread, Persona} = mailStore;
            const externalRecipients = new Set();
            const checkedPartnerIds = new Set();

            const checkPartner = (partnerId) => {
                if (!partnerId || checkedPartnerIds.has(partnerId)) {
                    return;
                }
                checkedPartnerIds.add(partnerId);
                const persona = Persona.get({type: "partner", id: partnerId});
                if (persona && !persona.isInternalUser) {
                    const name = persona.name || persona.email;
                    if (name) {
                        externalRecipients.add(name);
                    }
                }
            };

            this._addWizardRecipients(checkPartner);
            await this._addThreadRecipients(checkPartner, Thread);

            return [...externalRecipients];
        },

        _addWizardRecipients(checkPartner) {
            const partnerIdsField = this.props.record.data.partner_ids;
            if (!partnerIdsField || !partnerIdsField.records) {
                return;
            }
            for (const partnerRecord of partnerIdsField.records) {
                checkPartner(partnerRecord.data.id || partnerRecord.resId);
            }
        },

        async _addThreadRecipients(checkPartner, Thread) {
            const isNote = this.props?.record?.data?.subtype_is_log;
            if (isNote) {
                return;
            }
            const model = this.props.record.data.model;
            const threadId = this._getThreadId();

            if (!model || !threadId) {
                return;
            }
            const thread = await Thread.getOrFetch({model, id: threadId});
            if (!thread) {
                return;
            }
            const recipients = [
                ...(thread.recipients || []),
                ...(thread.followers || []),
            ];
            for (const recipient of recipients) {
                if (recipient.partner) {
                    checkPartner(recipient.partner.id);
                }
            }
        },

        _getThreadId() {
            let resIds = [];
            try {
                resIds = JSON.parse(this.props.record.data.res_ids || "[]");
            } catch {
                // Leave empty
            }
            return Array.isArray(resIds) && resIds.length ? resIds[0] : undefined;
        },
    });
}
