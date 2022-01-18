odoo.define('product_attribute_description.product_attribute_description', function (require) {
'use strict';
	
	$('[data-toggle="tooltip"]').tooltip('show').tooltip('hide');
	
	$('[data-toggle="tooltip"]').on({
	  "click": function() {		
	    $(this).tooltip('show');
	  }
	});
	
	
});


