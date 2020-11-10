odoo.define('abandoned_carts.FormController', function (require) {
"use strict";

var FormController = require('web.FormController');

FormController.include({
	_callButtonAction: function (attrs, record) {
		if (this.modelName=='customer.wizard' && attrs.name=='action_remove_customer_manual'){
			
			var ctx = attrs.context || {};
			var $selectedRows = this.$('tbody .o_list_record_selector input:checked').closest('tr');
			var selected_ids = _.map($selectedRows, function (row) {return $(row).data('id');});
			_.map(this.initialState.data.customer_ids.data,function(row){return row.id});
			
			var records = this.initialState.data.customer_ids.data.filter(function(row){return selected_ids.indexOf(row.id) >= 0})
			ctx['deleting_ids'] = _.map(records,function(rec){return rec.res_id})
			attrs.context = ctx;
		}
		return this._super(attrs, record)
	},
});

});
