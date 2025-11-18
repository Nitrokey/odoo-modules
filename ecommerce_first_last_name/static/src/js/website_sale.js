/** @odoo-module **/

import websiteSaleAddress from "@website_sale/js/address";

websiteSaleAddress.include({
    /**
     * Register change events for radio buttons.
     */
    events: Object.assign({}, websiteSaleAddress.prototype.events, {
        "change #company_type_individual": "_onChangeCompanyType",
        "change #company_type_company": "_onChangeCompanyType",
    }),

    /**
     * Toggle visibility of company & VAT fields based on selection.
     * Also make company name required if company type = 'company'.
     */
    _onChangeCompanyType(ev) {
        const target = ev.target;
        if (!["company_type_individual", "company_type_company"].includes(target.id)) {
            return;
        }

        const isCompany = target.value === "company";

        const companyDiv = this.el.querySelector("#company_name_div");
        const vatDiv = this.el.querySelector("#div_vat");
        const companyInput = this.el.querySelector("#o_company_name");

        // Toggle visibility
        if (companyDiv) companyDiv.classList.toggle("d-none", !isCompany);
        if (vatDiv) vatDiv.classList.toggle("d-none", !isCompany);

        // Toggle "required" attribute dynamically
        if (companyInput) {
            companyInput.required = isCompany;
            if (!isCompany) {
                companyInput.required = false;
            }
        }
    },
});
