odoo.define('ecommerce_first_last_name.website_state', function(require) {
    "use strict";

	var sAnimations = require('website.content.snippets.animation');
	sAnimations.registry.WebsiteSale.include({
		read_events: _.extend({}, sAnimations.registry.WebsiteSale.prototype.read_events, {
    	'change #company_type': '_onChangeCompanyType',
		
    	}),
		_onChangeCompanyType: function (ev) {
	        debugger;
			var company = document.getElementById("address_company_name");
           	var vat = document.getElementById("address_tin_vat");

			if ($(ev.currentTarget).val()=='company'){
				company.style.display = "block";
    			vat.style.display = "block";
			}
			else{
				company.style.display = "none";
    			vat.style.display = "none";
			}
	    }
	});
});