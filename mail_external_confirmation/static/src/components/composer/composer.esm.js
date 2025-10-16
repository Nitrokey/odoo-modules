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

            // Get thread information for backend check
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

            // Check if there are external users among followers via backend
            // This is more reliable than frontend checks as it has direct database access
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
