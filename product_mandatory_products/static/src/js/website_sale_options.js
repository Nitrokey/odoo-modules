odoo.define('product_mandatory_products.website_sale_extend', function (require) {
'use strict';
	
	var core = require('web.core');
	var _t = core._t;
	var rpc = require('web.rpc');
	var OptionalProductsModal = require('sale.OptionalProductsModal');
	var MandatoryProductsModal = require('product_mandatory_products.MandatoryProductsModal');
	var weContext = require('web_editor.context');
	var sAnimations = require('website.content.snippets.animation');
	var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
	var website_sales = require('website_sale_options.website_sale');
	require('website_sale.website_sale');
	
	website_sales.include({
				
		_handleAdd: function ($form) {
	        var self = this;
			var is_mandatory = false;
	        this.$form = $form;
	        this.isWebsite = true;
	
	        var productSelector = [
	            'input[type="hidden"][name="product_id"]',
	            'input[type="radio"][name="product_id"]:checked'
	        ];
	
	        var productReady = this.selectOrCreateProduct(
	            $form,
	            parseInt($form.find(productSelector.join(', ')).first().val(), 10),
	            $form.find('.product_template_id').val(),
	            false
	        );
	
	        return productReady.done(function (productId) {
	            $form.find(productSelector.join(', ')).val(productId);
	            self.rootProduct = {
	                product_id: productId,
	                quantity: parseFloat($form.find('input[name="add_qty"]').val() || 1),
	                product_custom_attribute_values: self.getCustomVariantValues($form.find('.js_product')),
	                variant_values: self.getSelectedVariantValues($form.find('.js_product')),
	                no_variant_attribute_values: self.getNoVariantAttributeValues($form.find('.js_product'))
	            };
				
				
				rpc.query({
	                route: '/shop/is_mendatory_product',
	                params: {product_id: productId}
	            })
	            .then(function (res) {
					if(res && typeof(self.optionalProductsModal) == "undefined"){
						self.optionalProductsModal = new MandatoryProductsModal($form, {
		                rootProduct: self.rootProduct,
		                isWebsite: true,
		                okButtonText: _t('Next'),
		                cancelButtonText: _t('Continue Shopping aa'),
		                title: _t('Add to cart'),
						is_mandatory:true,
			            }).open();
						
						
			            self.optionalProductsModal.on('options_empty', null, self._onModalOptionsEmpty.bind(self));
			            self.optionalProductsModal.on('update_quantity', null, self._onOptionsUpdateQuantity.bind(self));
			            self.optionalProductsModal.on('confirm', null, self._onModalConfirm.bind(self));
			            self.optionalProductsModal.on('back', null, self._onModalBack.bind(self));
						$("tr.o_select_options").hide();
			            return self.optionalProductsModal.opened();
						
						
					}else{
						
						self.optionalProductsModal = new OptionalProductsModal($form, {
		                //rootProduct:self.optionalProductsModal.mandatory_products,
						rootProduct: self.rootProduct,
		                isWebsite: true,
		                okButtonText: _t('Proceed to Checkout'),
		                cancelButtonText: _t('Continue Shopping'),
		                title: _t('Add to cart'),
						is_mandatory:false,
			            }).open();
			
			            self.optionalProductsModal.on('options_empty', null, self._onModalOptionsEmpty.bind(self));
			            self.optionalProductsModal.on('update_quantity', null, self._onOptionsUpdateQuantity.bind(self));
			            self.optionalProductsModal.on('confirm', null, self._onModalConfirm.bind(self));
			            self.optionalProductsModal.on('back', null, self._onModalBack.bind(self));
			
			            return self.optionalProductsModal.opened();
						
					}
				});
				
	          
	        });
	    },

		_onModalConfirm: function () {
			if(this.optionalProductsModal.mandatory_products){
				if(this.optionalProductsModal.optonal_product){
					this._onModalSubmit(false);
				}else{
					this._onModalSubmit(true);
				} 
			}else{
				this._onModalSubmit(true);
			}
    	},
		
		_onModalBack: function () {
	      /*  this._onModalSubmit(true);*/
			var customValues = JSON.stringify(this.optionalProductsModal.getSelectedProducts());
		        this.$form.ajaxSubmit({
		            url:  '/shop/cart/update_option',
		            data: {
		                lang: weContext.get().lang,
		                custom_values: customValues,
						goToShop: true,
		            },
		            success: function (quantity) {
		                
		               var path = window.location.pathname.replace(/shop([\/?].*)?$/, "/shop");
		               window.location.pathname = path;
		                
		                var $quantity = $(".my_cart_quantity");
		                $quantity.parent().parent().removeClass("d-none", !quantity);
		                $quantity.html(quantity).hide().fadeIn(600);
		            }
		        });
			
	     },
		
		_onModalSubmit: function (goToShop){
				var customValues = JSON.stringify(this.optionalProductsModal.getSelectedProducts());
		        this.$form.ajaxSubmit({
		            url:  '/shop/cart/update_option',
		            data: {
		                lang: weContext.get().lang,
		                custom_values: customValues,
						goToShop: goToShop,
		            },
		            success: function (quantity) {
		                if (goToShop) {
		                    var path = window.location.pathname.replace(/shop([\/?].*)?$/, "shop/cart");
		                    window.location.pathname = path;
		                }
		                var $quantity = $(".my_cart_quantity");
		                $quantity.parent().parent().removeClass("d-none", !quantity);
		                $quantity.html(quantity).hide().fadeIn(600);
		            }
		        });
			
	     },
	

				
	})
	
});