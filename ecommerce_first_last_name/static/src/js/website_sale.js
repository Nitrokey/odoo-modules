// @odoo-module

import websiteSaleAddress from "@website_sale/js/address";

const NAME_MAX_LENGTH = 50;

websiteSaleAddress.include({
    /**
     * @override
     */
    start() {
        const def = this._super(...arguments);
        this.firstNameInput = this.addressForm.querySelector('input[name="name"]');
        this.lastNameInput = this.addressForm.querySelector('input[name="last_name"]');
        if (this.firstNameInput && this.lastNameInput) {
            const update = this._updateNameMaxLength.bind(this);
            this.firstNameInput.addEventListener("input", update);
            this.lastNameInput.addEventListener("input", update);
            update();
        }
        return def;
    },

    /**
     * The server stores "<first name> <last name>" as the partner name, so
     * both inputs share one budget, including the separating space.
     */
    _updateNameMaxLength() {
        const first = this.firstNameInput.value.length;
        const last = this.lastNameInput.value.length;
        this.firstNameInput.maxLength = Math.max(NAME_MAX_LENGTH - last - 1, 0);
        this.lastNameInput.maxLength = Math.max(NAME_MAX_LENGTH - first - 1, 0);
    },

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
