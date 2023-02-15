odoo.define('abandoned_carts.relational_fields', function (require) {
"use strict";

var registry = require('web.field_registry');

registry.get('one2many').include({
	_render: function () {
		if (this.value && (this.value.model=='res.partner' || this.value.model=='sale.order' ) && this.value.type=='list'){
			this.value.addHasSelectors=true;
		}
		return this._super()
	}

});

});