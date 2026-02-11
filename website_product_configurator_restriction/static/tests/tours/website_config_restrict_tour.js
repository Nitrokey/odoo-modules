/** @odoo-module **/

import {registry} from "@web/core/registry";
import * as tourUtils from "@website_sale/js/tours/tour_utils";

registry.category("web_tour.tours").add("website_configuration_restriction_tour", {
    url: "/shop",
    steps: () => [
        {
            content: "search 2 series",
            trigger: 'form input[name="search"]',
            run: "edit 2 series",
        },
        {
            content: "search 2 series",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
            run: "click",
        },
        {
            content: "select 2 series",
            trigger: '.oe_product_cart:first a:contains("2 series")',
            run: "click",
        },
        {
            content: "click to select Fuel",
            trigger: '.js_variant_change[data-value_name="Diesel"]',
            run: "click",
        },
        {
            content: "click to select Engine",
            trigger: '.js_variant_change[data-value_name="220d"]',
            run: "click",
        },
        {
            content: "click to select Lines",
            trigger: '.js_variant_change[data-value_name="Model Sport Line"]',
            run: "click",
        },
        {
            content: "click to select Color",
            trigger: '.js_variant_change[data-value_name="Black"]',
            run: "click",
        },
        {
            content: "click to select Rims",
            trigger: '.js_variant_change[data-value_name="V-spoke 18\\""]',
            run: "click",
        },
        {
            content: "click to select Tapistry",
            trigger: '.js_variant_change[data-value_name="Oyster/Black"]',
            run: "click",
        },
        {
            content: "click to select Transmission",
            trigger:
                '.js_variant_change[data-value_name="Automatic Sport (Steptronic)"]',
            run: "click",
        },
        {
            content: "click to select Options",
            trigger: '.js_variant_change[data-value_name="Armrest"]',
            run: "click",
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
            run: "click",
        },
        {
            content: "Proceed to checkout",
            trigger: "button:contains(Proceed to Checkout)",
            run: "click",
        },
        tourUtils.goToCart({quantity: 1}),
        tourUtils.goToCheckout(),
    ],
});
