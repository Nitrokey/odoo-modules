odoo.define("product_mandatory_products.website_sale_options", function (require) {
  "use strict";

  var ajax = require("web.ajax");
  var rpc = require("web.rpc");
  var publicWidget = require("web.public.widget");
  var OptionalProductsModal = require("sale_product_configurator.OptionalProductsModal");
  require("website_sale_options.website_sale");

  publicWidget.registry.WebsiteSale.include({
    _getContext: function (extra, extraContext) {
      var res = this._super(extra, extraContext);
      if (this.optionalProductsModal && this.optionalProductsModal.display_optional) {
        res.display_optional = this.optionalProductsModal.display_optional;
      }
      return res;
    },
    //    Overwrite to add `goToShop` custom value in ajax call
    _onModalSubmit: function (goToShop) {
      let currency = "";
      goToShop = !this.optionalProductsModal.display_optional; // eslint-disable-line no-param-reassign
      const $product = $("#product_detail");
      if ($product.length) {
        currency = $product.data("product-tracking-info").currency;
      } else {
        // Add to cart from /shop page
        currency = this.$('[itemprop="priceCurrency"]').first().text();
      }
      const productsTrackingInfo = [];
      this.$(".js_product.in_cart").each((i, el) => {
        productsTrackingInfo.push({
          item_id: el.getElementsByClassName("product_id")[0].value,
          item_name: el.getElementsByClassName("product_display_name")[0].textContent,
          quantity: el.getElementsByClassName("js_quantity")[0].value,
          currency: currency,
          price: el
            .getElementsByClassName("oe_price")[0]
            .getElementsByClassName("oe_currency_value")[0].textContent,
        });
      });
      if (productsTrackingInfo) {
        this.$el.trigger("add_to_cart_event", productsTrackingInfo);
      }

      this.optionalProductsModal.getAndCreateSelectedProducts().then((products) => {
        const productAndOptions = JSON.stringify(products);
        ajax
          .post("/shop/cart/update_option", {
            product_and_options: productAndOptions,
            goto_shop: goToShop,
          })
          .then(function (quantity) {
            if (goToShop) {
              window.location.pathname = "/shop/cart";
            }
            const $quantity = $(".my_cart_quantity");
            $quantity.parent().parent().removeClass("d-none");
            $quantity.text(quantity).hide().fadeIn(600);
          });
      });
    },
  });

  OptionalProductsModal.include({
    //       Overwrite
    //       Get all product inside cart and send to controller to check for mandatory product.
    _onConfirmButtonClick: function () {
      var self = this;
      var products = [];
      this.$modal.find(".js_product.in_cart:not(.main_product)").each(function () {
        var $item = $(this);
        products.push(parseInt($item.find("input.product_id").val(), 10));
      });
      rpc
        .query({
          route: "/shop/check_mendatory_product",
          params: {
            products: products,
            root_product: this.rootProduct.product_id,
            current_context: this.context,
          },
        })
        .then(function (res) {
          if (res.has_mandatory) {
            $("#mandatory_msg").css("display", "none");
            self.display_optional = res.display_optional;
            self.trigger("confirm");
            self.close();
            if (res.display_optional) {
              document.getElementById("add_to_cart").click();
            }
          } else {
            $("#mandatory_msg").css("display", "block");
            return false;
          }
        });
    },
  });

  return publicWidget.registry.WebsiteSaleOptions;
});
