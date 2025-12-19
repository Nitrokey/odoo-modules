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
        if (this.props.type === "message" || this.props.type === "note") {
            const res_id = this.props.composer?.thread?.id;
            const model = this.props.composer?.thread?.model;

            if (!res_id || !model) {
                console.warn("Missing thread info, sending without confirmation");
                super.sendMessage();
                return;
            }

            // Prepare check data
            const checkData = {
                rec_id: res_id,
                model: model,
            };

            // Add mentioned partner IDs for notes
            if (this.props.type === "note") {
                var mentionedPartners = this.props.composer?.mentionedPartners || null;
                const partnerIds = this._extractPartnerIds(mentionedPartners);

                if (partnerIds.length > 0) {
                    checkData.mentioned_partner_ids = partnerIds;
                } else {
                    super.sendMessage();
                    return;
                }
            }

            // Make a single RPC call to check everything
            try {
                const result = await rpc("/message/external_users/check", checkData);

                if (result.needs_confirmation) {
                    await this._showConfirmationDialog(result.confirmation_message);
                } else {
                    super.sendMessage();
                }
            } catch (error) {
                console.error("External check failed:", error);
                super.sendMessage();
            }
        } else {
            super.sendMessage();
        }
    },

    /**
     * Extract partner IDs from mentionedPartners
     */
    _extractPartnerIds(mentionedPartners) {
        if (!mentionedPartners?.data?.length) {
            return [];
        }

        return mentionedPartners.data
            .map((item) => {
                if (typeof item === "string") {
                    const match = item.match(/AND\s+(\d+)$/);
                    return match ? parseInt(match[1], 10) : null;
                } else if (item && typeof item === "object") {
                    return item.id || item.resId || item.partner_id;
                }
                return null;
            })
            .filter((id) => id !== null);
    },

    /**
     * Show confirmation dialog
     */
    async _showConfirmationDialog(message) {
        return new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                title: _t("External Partner Confirmation"),
                body: message,
                confirmLabel: _t("Send"),
                cancelLabel: _t("Cancel"),
                confirm: async () => {
                    super.sendMessage();
                    resolve();
                },
                cancel: () => {
                    resolve();
                },
            });
        });
    },
});
