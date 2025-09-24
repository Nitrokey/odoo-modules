/** @odoo-module */

import {Composer} from "@mail/components/composer/composer";
import {patch} from "web.utils";
import core from "web.core";
import Dialog from "web.Dialog";
import rpc from "web.rpc";
const _t = core._t;

patch(
    Composer.prototype,
    "mail_external_confirmation/static/src/components/composer/composer.js",
    {
        /**
         * Override to show confirmation dialog when sending messages to external users.
         *
         * @override
         */
        _onClickSend() {
            const superMethod = this._super;

            // Check if it's a log message - no confirmation needed
            if (this.composerView.composer.isLog) {
                this._super();
                return;
            }

            // First check if there are selected recipients in the composer UI
            const hasExternalRecipients = this._checkExternalRecipients();

            if (hasExternalRecipients) {
                this._showConfirmationDialog(superMethod);
                return;
            }

            // If no external recipients detected in UI, check followers via backend
            const thread =
                this.composerView &&
                this.composerView.composer &&
                this.composerView.composer.thread;
            if (!thread || !thread.__values || !thread.__values.fetchMessagesParams) {
                console.warn(
                    "mail_external_confirmation: Thread data not available, sending without confirmation"
                );
                this._super();
                return;
            }

            const res_id = thread.__values.fetchMessagesParams.thread_id;
            const model = thread.__values.fetchMessagesParams.thread_model;

            if (!res_id || !model) {
                console.warn(
                    "mail_external_confirmation: Missing thread_id or thread_model, sending without confirmation"
                );
                this._super();
                return;
            }

            // Check if there are external users among followers with proper error handling
            rpc.query({
                model: "res.partner",
                method: "check_users",
                args: [res_id, model],
            })
                .then((hasExternalUsers) => {
                    if (hasExternalUsers) {
                        this._showConfirmationDialog(superMethod);
                    } else {
                        // No external users, send directly
                        superMethod();
                    }
                })
                .catch((error) => {
                    console.error(
                        "mail_external_confirmation: Error checking external users:",
                        error
                    );
                    // On error, send without confirmation to avoid blocking the user
                    superMethod();
                });
        },

        /**
         * Check if there are external recipients selected in the composer UI
         * This handles the "Send to customer" checkbox scenario
         */
        _checkExternalRecipients() {
            try {
                const composer = this.composerView.composer;

                // Check if there are recipients selected
                if (composer.recipients && composer.recipients.length > 0) {
                    // Check if any recipient is external (not an internal user)
                    for (const recipient of composer.recipients) {
                        if (this._isExternalRecipient(recipient)) {
                            return true;
                        }
                    }
                }

                // Check for partner recipients
                if (composer.partners && composer.partners.length > 0) {
                    for (const partner of composer.partners) {
                        if (this._isExternalPartner(partner)) {
                            return true;
                        }
                    }
                }

                // Check for suggested recipients (common in chatter)
                if (
                    composer.suggestedRecipients &&
                    composer.suggestedRecipients.length > 0
                ) {
                    for (const recipient of composer.suggestedRecipients) {
                        if (recipient.checked && this._isExternalRecipient(recipient)) {
                            return true;
                        }
                    }
                }

                return false;
            } catch (error) {
                console.warn(
                    "mail_external_confirmation: Error checking external recipients:",
                    error
                );
                return false;
            }
        },

        /**
         * Check if a recipient is external
         */
        _isExternalRecipient(recipient) {
            // If recipient has no user_ids or is not an internal user
            if (!recipient.user_ids || recipient.user_ids.length === 0) {
                return true; // No user account = external
            }

            // Check if recipient is marked as external or customer
            if (recipient.is_company === false && recipient.customer_rank > 0) {
                return true;
            }

            return false;
        },

        /**
         * Check if a partner is external
         */
        _isExternalPartner(partner) {
            if (!partner) return false;

            // Partners without users are external
            if (!partner.user_ids || partner.user_ids.length === 0) {
                return true;
            }

            // Check if it's marked as a customer
            if (partner.customer_rank && partner.customer_rank > 0) {
                return true;
            }

            return false;
        },

        /**
         * Show the confirmation dialog
         */
        _showConfirmationDialog(superMethod) {
            this.dialog = new Dialog(this, {
                title: _t("Confirmation For Chatter"),
                size: "medium",
                $content: $("<div/>", {
                    html: _t(
                        "<p>Your message will be sent to external partners (e.g. customers).</p>"
                    ),
                }),
                buttons: [
                    {
                        text: _t("Send"),
                        classes: "btn-primary",
                        close: true,
                        click: function () {
                            superMethod();
                        },
                    },
                    {text: _t("Cancel"), close: true},
                ],
            });
            this.dialog.open();
        },
    }
);
