/** @odoo-module **/

import VariantMixin from "@website_sale/js/sale_variant_mixin";
import { rpc } from "@web/core/network/rpc";

// Store the original method
const originalHandleCustomValues = VariantMixin.handleCustomValues;

VariantMixin.handleCustomValues = function ($target) {
    const $parent = $target.closest('.js_product');
    const productTemplateId = parseInt($parent.find('.product_template_id').val());
    console.log('\n\n $parent-------------', $parent)
    console.log('\n\n productTemplateId-------------', productTemplateId)

    // Find variant container and custom input
    let $variantContainer;
    let $customInput = false;

    if ($target.is('input[type=radio]') && $target.is(':checked')) {
        $variantContainer = $target.closest('ul').closest('li');
        $customInput = $target;
    } else if ($target.is('select')) {
        $variantContainer = $target.closest('li');
        $customInput = $target.find(`option[value="${$target.val()}"]`);
        console.log('\n\n $customInput-------------', $customInput)
    }

    if ($variantContainer && $customInput) {
        const attributeId = $variantContainer.data('attribute_id');
        const PTAVId = $customInput.data('value_id');
        const formData = $parent.find('input, select, textarea').serializeArray();
        
        // Only run restriction check if we have valid IDs
        if (productTemplateId && attributeId && PTAVId) {
            rpc("/check/configurator/restriction", {
                'product_template_id': productTemplateId,
                'attribute_id': attributeId,
                'ptav_id': PTAVId,
                'form_data': formData,
            }).then(data => {
                if (data?.is_configured) {
                    this._applyAttributeRestrictions(data.domain);
                }
            });
        }
    }

    // Call original method for custom value handling
    return originalHandleCustomValues.call(this, $target);
};

// Helper method to apply restrictions
VariantMixin._applyAttributeRestrictions = function (domainData) {
    console.log('\n\n domainData-------------',domainData)
    _.each(domainData, (valueArray, attributeName) => {
        const [allOptions, allowedOptions] = valueArray;
        const $selectOptions = $(`option[data-attribute_name="${attributeName}"]`);
        const $radioOptions = $(`input[data-attribute_name="${attributeName}"]`);
        const $allOptions = [...$selectOptions, ...$radioOptions];
        
        if (!$allOptions.length) return;
        
        let activeSelected = false;
        
        $allOptions.forEach(opt => {
            const $opt = $(opt);
            const valueName = $opt.data('value_name');
            const isAllowed = allowedOptions.includes(valueName);
            
            $opt.prop('disabled', !isAllowed);
            
            // Deselect if disabled and currently selected
            if (!isAllowed && (
                ($opt.is('option') && $opt.is(':selected')) ||
                (($opt.is(':radio') || $opt.is(':checkbox')) && $opt.is(':checked'))
            )) {
                $opt.prop('selected', false).prop('checked', false);
            } else if (isAllowed && (
                $opt.is(':selected') || $opt.is(':checked')
            )) {
                activeSelected = true;
            }
        });
        
        // Auto-select first allowed if none selected
        if (!activeSelected) {
            const $firstAllowed = $allOptions
                .filter(opt => allowedOptions.includes($(opt).data('value_name')))
                .map(opt => $(opt))
                .find($opt => true); // Get first element
            
            if ($firstAllowed) {
                $firstAllowed.prop('selected', true).prop('checked', true);
            }
        }
    });
};
