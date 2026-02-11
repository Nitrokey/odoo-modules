/** @odoo-module **/

import {WebsiteSale} from "@website_sale/js/website_sale";
import {rpc} from "@web/core/network/rpc";

WebsiteSale.include({
    _handleAdd: function ($form) {
        var self = this;
        this.$form = $form;

        var productSelector = [
            'input[type="hidden"][name="product_id"]',
            'input[type="radio"][name="product_id"]:checked',
        ];

        var productReady = this.selectOrCreateProduct(
            $form,
            parseInt($form.find(productSelector.join(", ")).first().val(), 10),
            $form.find(".product_template_id").val(),
            false
        );

        return productReady.then(function (productId) {
            $form.find(productSelector.join(", ")).val(productId);

            self.rootProduct = {
                product_id: productId,
                product_template_id: parseInt($form.find(".product_template_id").val()),
                quantity: parseFloat($form.find('input[name="add_qty"]').val() || 1),
                product_custom_attribute_values: self.getCustomVariantValues(
                    $form.find(".js_product")
                ),
                variant_values: self.getSelectedVariantValues(
                    $form.find(".js_product")
                ),
                no_variant_attribute_values: self.getNoVariantAttributeValues(
                    $form.find(".js_product")
                ),
                config_session_id: $form.find('input[name="config_session_id"]').val(),
            };

            return self._onProductReady();
        });
    },

    handleCustomValues: function ($target) {
        this._super.apply(this, arguments);
        // Find variant container and custom input
        let $variantContainer = false;
        let $customInput = false;

        if ($target.is("input[type=radio]") && $target.is(":checked")) {
            $variantContainer = $target.closest("ul").closest("li");
            $customInput = $target[0];
        } else if ($target.is("select")) {
            $variantContainer = $target[0].closest("li");
            $customInput = $target.find(`option[value="${$target.val()}"]`);
        }

        if ($variantContainer && $customInput) {
            const $parent = $target.closest(".js_product");
            const productTemplateId = parseInt(
                $parent.find(".product_template_id").val()
            );
            const attributeId = $variantContainer[0].dataset.attribute_id;
            const PTAVId = $customInput.dataset.value_id;
            const formData = $parent.find("input, select, textarea").serializeArray();

            // Only run restriction check if we have valid IDs
            if (productTemplateId && attributeId && PTAVId) {
                rpc("/check/configurator/restriction", {
                    product_template_id: productTemplateId,
                    attribute_id: attributeId,
                    ptav_id: PTAVId,
                    form_data: formData,
                }).then((data) => {
                    if (data?.is_configured) {
                        this._applyAttributeRestrictions(data.domain);
                    }
                });
            }
        }
    },

    // Helper method to apply restrictions
    _applyAttributeRestrictions: function (domainData) {
        Object.entries(domainData).forEach(([attributeName, valueArray]) => {
            const [, allowedOptions] = valueArray;
            const $selectOptions = $(`option[data-attribute_name="${attributeName}"]`);
            const $radioOptions = $(`input[data-attribute_name="${attributeName}"]`);
            const $allOptions = [...$selectOptions, ...$radioOptions];

            if (!$allOptions.length) return;

            let activeSelected = false;
            $allOptions.forEach((opt) => {
                const $opt = $(opt);
                const valueName = $opt.data("value_name");
                const isAllowed = allowedOptions.includes(valueName);
                $opt.prop("disabled", !isAllowed);

                // Deselect if disabled and currently selected
                if (!isAllowed) {
                    if ($opt.is("option") && $opt.is(":selected")) {
                        $opt.prop("selected", false);
                    } else if (
                        ($opt.is(":radio") || $opt.is(":checkbox")) &&
                        $opt.is(":checked")
                    ) {
                        $opt.prop("checked", false).trigger("change");
                    }
                } else if ($opt.is(":selected") || $opt.is(":checked")) {
                    activeSelected = true;
                }
            });

            // Auto-select first allowed if none selected
            if (!activeSelected) {
                const firstAllowed = $allOptions.find((opt) => {
                    const $opt = $(opt);
                    const valueName = $opt.data("value_name");
                    return (
                        valueName !== undefined && allowedOptions.includes(valueName)
                    );
                });

                if (firstAllowed) {
                    const $firstAllowed = $(firstAllowed);
                    if ($firstAllowed.is("option")) {
                        $firstAllowed.prop("selected", true).parent().trigger("change");
                    } else {
                        $firstAllowed.prop("checked", true).trigger("change");
                    }
                }
            }
        });
    },
});
