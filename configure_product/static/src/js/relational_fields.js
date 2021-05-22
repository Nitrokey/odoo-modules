odoo.define('configure_product.relational_fields', function (require) {
"use strict";

var relational_fields = require('web.relational_fields');

relational_fields.FieldOne2Many.include({
	
	_onAddRecord: function (ev) {
		var data = ev.data || {};
		if (this.model=='purchase.order' && data.context && data.context.length>0){
			data.context.forEach(function (item, index) {
				if (item.default_product_uom_qty!= undefined){
					item.default_product_qty = item.default_product_uom_qty;
			  	}
			});
			ev.data.context= data.context;
		}
		return this._super(ev);
	},
});
});