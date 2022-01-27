odoo.define('configure_product.product_configure_wizard', function (require) {
"use strict";

	var FormController = require('web.FormController');
	var FormRenderer = require('web.FormRenderer');

	FormRenderer.include({
        _onClickConfigureProduct: function (event){
            var active_id = this.state.res_id;
            if (typeof val == "undefined"){
                var active_id = false;
            }

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
		_updateView: function ($newContent) {
		    debugger;
		    if(this.state.model == "mrp.production" && this.state.data.state == "confirmed"){
                var $configure_button1 = $("<button type='button' class='btn btn-link o_form_button_configure_product1' accesskey='cf'>Configure a product</button>");
                $configure_button1.attr('data-active-id', this.state.res_id);
                $newContent.find("[name='product_id']").after($configure_button1)
                this.$el.on('click', '.o_form_button_configure_product1', this._onClickConfigureProduct.bind(this));
		    }
            this._super($newContent);
		},
	})
//	    renderButtons: function ($node) {
//			this._super($node)
//			if (this.modelName==='mrp.production' && !this.noLeaf){
//				var $configure_button1 = $("<button type='button' class='btn btn-link o_form_button_configure_product1' accesskey='cf'>Configure a product</button>");
//				var $configure_button2 = $("<button type='button' class='btn btn-link o_form_button_configure_product2' accesskey='cf'>Configure a product</button>");
//				this.$buttons.find(".o_form_button_cancel").after($configure_button1);
//				this.$buttons.find(".o_form_button_create").after($configure_button2);
//				this.$buttons.on('click', '.o_form_button_configure_product1', this._onClickConfigureProduct.bind(this));
//				this.$buttons.on('click', '.o_form_button_configure_product2', this._onClickConfigureProduct.bind(this));
//			}
//		},
});
