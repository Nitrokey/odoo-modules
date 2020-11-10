odoo.define('abandoned_carts.ListRenderer', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');

ListRenderer.include({
	init: function (parent, state, params) {
		if (state.addHasSelectors){
			params.hasSelectors=true;
		}
		return this._super(parent, state, params);
	}
});

});
