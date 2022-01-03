odoo.define('configure_product.product_configure', function (require) {
"use strict";
	
	var ProductConfiguratorFormController = require('sale.ProductConfiguratorFormController');
	
	ProductConfiguratorFormController.include({
		_handleAdd: function ($modal) {
			var context = this.model.get(this.handle, {raw: true});
			var ctx = context.getContext();
			
			if (ctx.config_product === true) {
				var self = this;
		        var productSelector = [
		            'input[type="hidden"][name="product_id"]',
		            'input[type="radio"][name="product_id"]:checked'
		        ];

				var productId = parseInt($modal.find(productSelector.join(', ')).first().val(), 10);
				var quantity = parseFloat($modal.find('input[name="add_qty"]').val() || 1)
				this._rpc({
		            route: '/product_configure',
		            params: {
		                product_id: productId,
						active_id: ctx.active_id,
						quantity: quantity,
		            }
		        }).then(function () {
					return self.do_action({ type: 'ir.actions.act_window_close' });
		        });

	        } else {
				this._super.apply(this, arguments);
	        }
		},
	});
	
});
