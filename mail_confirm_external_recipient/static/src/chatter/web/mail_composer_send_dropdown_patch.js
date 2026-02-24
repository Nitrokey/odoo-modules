/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";

const widget = registry.category("view_widgets").get("mail_composer_send_dropdown");
const MailComposerSendDropdown = widget?.component;

if (MailComposerSendDropdown) {
    const superOnClickSend = MailComposerSendDropdown.prototype.onClickSend;

    patch(MailComposerSendDropdown.prototype, {
        async onClickSend() {
            try {
                const mailStore = this.env.services["mail.store"];
                const {Thread, Persona} = mailStore;

                const model = this.props.record.data.model;
                const isNote = this.props?.record?.data?.subtype_is_log;
                let resIds = [];
                try {
                    resIds = JSON.parse(this.props.record.data.res_ids || "[]");
                } catch (_) {
                    // Leave empty
                }
                const threadId =
                    Array.isArray(resIds) && resIds.length ? resIds[0] : undefined;

                const externalRecipients = [];
                const checkedPartnerIds = new Set();
                const checkPartner = (partnerId) => {
                    if (!partnerId || checkedPartnerIds.has(partnerId)) {
                        return;
                    }
                    checkedPartnerIds.add(partnerId);
                    const persona = Persona.get({type: "partner", id: partnerId});
                    // If persona is available, use it to determine internal/external
                    if (persona && !persona.isInternalUser) {
                        const name = persona.name || persona.email;
                        if (name && !externalRecipients.includes(name)) {
                            externalRecipients.push(name);
                        }
                    }
                };

                // 1. Check final recipients from the wizard (manually added)
                const partnerIdsField = this.props.record.data.partner_ids;
                if (partnerIdsField && partnerIdsField.records) {
                    for (const partnerRecord of partnerIdsField.records) {
                        checkPartner(partnerRecord.data.id || partnerRecord.resId);
                    }
                }

                // 2. Check thread recipients (e.g. followers)
                // These are displayed in the MailComposerRecipientList and cannot be removed
                if (!isNote && model && threadId) {
                    const thread = await Thread.getOrFetch({model, id: threadId});
                    if (thread) {
                        // Check thread.recipients (if populated)
                        if (thread.recipients) {
                            for (const follower of thread.recipients) {
                                if (follower.partner) {
                                    checkPartner(follower.partner.id);
                                }
                            }
                        }
                        // Check thread.followers as a fallback for "non-removable followers"
                        if (thread.followers) {
                            for (const follower of thread.followers) {
                                if (follower.partner) {
                                    checkPartner(follower.partner.id);
                                }
                            }
                        }
                    }
                }

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
    });
}
