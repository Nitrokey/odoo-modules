// @odoo-module
import {patch} from "@web/core/utils/patch";
import {threadActionsRegistry} from "@mail/core/common/thread_actions";

// Extend the "settings" action condition to also show in the Discuss app
const settingsAction = threadActionsRegistry.get("settings");
if (settingsAction) {
    const originalCondition = settingsAction.condition;
    patch(settingsAction, {
        condition(component) {
            const baseCondition = originalCondition.call(this, component);
            // Also allow settings in the Discuss app
            return (
                baseCondition ||
                (component.thread?.allowCalls && component.env.inDiscussApp)
            );
        },
    });
}
