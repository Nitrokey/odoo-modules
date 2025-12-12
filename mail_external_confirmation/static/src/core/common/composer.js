/** @odoo-module **/

import {Composer} from "@mail/core/common/composer";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";
import {useService} from "@web/core/utils/hooks";

patch(Composer.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
    },

    async sendMessage() {
        if (this.props.type === "message") {
            // Get thread information for backend check
            const res_id = this.props.composer?.thread?.id;
            const model = this.props.composer?.thread?.model;

            if (!res_id || !model) {
                console.warn(
                    "mail_external_confirmation: Missing thread_id or thread_model, sending without confirmation"
                );
                // Fallback to original behavior on error
                super.sendMessage();
                return;
            }

            // Call controller to check for external users
            await rpc("/message/external_users/check", {
                rec_id: res_id,
                model: model,
            })
                .then((hasExternalUsers) => {
                    if (hasExternalUsers) {
                        // Show confirmation dialog before sending to external partners
                        this.dialog.add(ConfirmationDialog, {
                            title: _t("Confirmation For Chatter"),
                            body: _t(
                                "Your message will be sent to external partners (e.g. customers)."
                            ),
                            confirmLabel: _t("Send"),
                            cancelLabel: _t("Cancel"),
                            confirm: async () => {
                                super.sendMessage();
                            },
                            cancel: () => {
                                // Empty function to display the cancel button
                            },
                        });
                    } else {
                        // No external users, send directly
                        super.sendMessage();
                    }
                })
                .catch((error) => {
                    // On error, send without confirmation to avoid blocking the user
                    console.error("External user check failed:", error);
                    // Fallback to original behavior on error
                    super.sendMessage();
                });
        } else {
            super.sendMessage();
        }
    },
});
