/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";

publicWidget.registry.WebsiteSale.include({
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
        // This._super.apply(this, arguments);
        console.log("\n\n My $target-----------", $target);
        const $parent = $target.closest(".js_product");
        const productTemplateId = parseInt($parent.find(".product_template_id").val());
        // Console.log('\n\n productTemplateId-------------', productTemplateId)

        // Find variant container and custom input
        let $variantContainer;
        let $customInput = false;

        if ($target.is("input[type=radio]") && $target.is(":checked")) {
            $variantContainer = $target.closest("ul").closest("li");
            $customInput = $target[0];
        } else if ($target.is("select")) {
            $variantContainer = $target[0].closest("li");
            $customInput = $target.find(`option[value="${$target.val()}"]`);
            // Console.log('\n\n 111111 $customInput-------------', $customInput)
        }

        // Console.log('\n\n 2222 $variantContainer---------------', $variantContainer)
        // console.log('\n\n 4444 $customInput---------------', $customInput)
        if ($variantContainer && $customInput) {
            const attributeId = $variantContainer[0].dataset.attribute_id;
            // Console.log('\n\n 4444 attributeId---------------', attributeId)
            const PTAVId = $customInput.dataset.value_id;
            // Console.log('\n\n 4444 PTAVId---------------', PTAVId)
            const formData = $parent.find("input, select, textarea").serializeArray();
            // Console.log('\n\n 4444 formData---------------', formData)

            // Only run restriction check if we have valid IDs
            if (productTemplateId && attributeId && PTAVId) {
                rpc("/check/configurator/restriction", {
                    product_template_id: productTemplateId,
                    attribute_id: attributeId,
                    ptav_id: PTAVId,
                    form_data: formData,
                }).then((data) => {
                    console.log("\n\n REST data------------", data);
                    if (data?.is_configured) {
                        this._applyAttributeRestrictions(data.domain);
                    }
                });
            }
        }
    },

    // Helper method to apply restrictions
    _applyAttributeRestrictions: function (domainData) {
        console.log("\n\n domainData--------------", domainData);
        // // Validate input
        // if (!Array.isArray(domainData)) {
        //     console.warn('Invalid domainData received:', domainData);
        //     return;
        // }

        domainData.forEach((restriction) => {
            console.log("\n\n restriction--------------", restriction);
            const [attributeName, valueArray] = restriction;
            const [allOptions, allowedOptions] = valueArray;
            const $selectOptions = $(`option[data-attribute_name="${attributeName}"]`);
            const $radioOptions = $(`input[data-attribute_name="${attributeName}"]`);
            const $allOptions = [...$selectOptions, ...$radioOptions];
            console.log("\n\n $allOptions--------------", $allOptions);
            console.log("\n\n $radioOptions--------------", $radioOptions);
            console.log("\n\n $selectOptions--------------", $selectOptions);

            if (!$allOptions.length) return;

            let activeSelected = false;
            $allOptions.forEach((opt) => {
                const $opt = $(opt);
                const valueName = $opt.dataset.value_name;
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
                    const valueName = $opt.dataset.value_name;
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
