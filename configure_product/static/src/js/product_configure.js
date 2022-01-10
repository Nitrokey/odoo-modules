odoo.define('configure_product.product_configure', function (require) {
"use strict";
	
	var ProductConfiguratorFormController = require('sale.ProductConfiguratorFormController');
	var rpc = require('web.rpc');
	
	ProductConfiguratorFormController.include({
		_handleAdd: function ($modal) {
			var context = this.model.get(this.handle, {raw: true});
			var ctx = context.getContext();
			
			if (ctx.config_product === true) {
		        var productSelector = [
		            'input[type="hidden"][name="product_id"]',
		            'input[type="radio"][name="product_id"]:checked'
		        ];

				var product_id = parseInt($modal.find(productSelector.join(', ')).first().val(), 10);
				var quantity = parseFloat($modal.find('input[name="add_qty"]').val() || 1)
				
				if (ctx.active_id){
					this._rpc({
			            route: '/product_configure',
			            params: {
			                product_id: product_id,
							active_id: ctx.active_id,
							quantity: quantity,
			            }
			        }).then(function () {
						window.location.reload();
			        });
				} else {
					this._rpc({
		                model: 'mrp.production',
		                method: 'return_active_id',
						args: ['',product_id, quantity],
		            }).then(function (url) {
						window.location.href = url;
			        });
				}
	        } else {
				this._super.apply(this, arguments);
	        }
		},
	});
	
});
