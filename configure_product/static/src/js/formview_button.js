odoo.define('configure_product.product_configure_wizard', function (require) {
"use strict";

	var FormController = require('web.FormController');

	FormController.include({
		renderButtons: function ($node) {
			this._super($node)
			if (this.modelName==='mrp.production' && !this.noLeaf){
				var $configure_button1 = $("<button type='button' class='btn btn-link o_form_button_configure_product1' accesskey='cf'>Configure a product</button>");
				var $configure_button2 = $("<button type='button' class='btn btn-link o_form_button_configure_product2' accesskey='cf'>Configure a product</button>");
				this.$buttons.find(".o_form_button_cancel").after($configure_button1);
				this.$buttons.find(".o_form_button_create").after($configure_button2);
				this.$buttons.on('click', '.o_form_button_configure_product1', this._onClickConfigureProduct.bind(this));
				this.$buttons.on('click', '.o_form_button_configure_product2', this._onClickConfigureProduct.bind(this));
			}
		},
		_onClickConfigureProduct : function (event) {
	        event.stopPropagation();
			var context = this.model.get(this.handle, {raw: true});			
			var active_id = context.data.id
			
	        return this.do_action({
	            name: "Configure a product",
	            type: 'ir.actions.act_window',
				res_model: 'sale.product.configurator',
				view_type: 'form',
				view_mode: 'form',
	            views: [[false, 'form']],
	            target: 'new',
				context: {'config_product': true, 'active_id': active_id},
	        });
	    },
	});
});
