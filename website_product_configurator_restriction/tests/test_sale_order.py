from ..tests.test_website_product_configurator_restriction import (
    ProductConfiguratorRestrictionTestCases,
)


class TestSaleOrder(ProductConfiguratorRestrictionTestCases):
    def setUp(self):
        super().setUp()
        self.partner = self.env.ref("base.res_partner_1")
        self.product = self.env["product.product"].create({"name": "Test Product"})
        self.product_uom_unit = self.env.ref("uom.product_uom_unit")
        self.sale_order = self.env["sale.order"].create(
            {
                "name": "Test SO",
                "partner_id": self.partner.id,
                "partner_invoice_id": self.partner.id,
                "partner_shipping_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": "Test Line",
                            "product_uom": self.product_uom_unit.id,
                            "product_uom_qty": 2.0,
                            "price_unit": 400.00,
                            "config_session_id": self.session_id.id,
                        },
                    ),
                ],
            }
        )

    def test_cart_update(self):
        product_id = (
            self.sale_order.order_line.product_id.product_tmpl_id.product_variant_id.id
        )
        self.sale_order._cart_update(
            product_id=product_id,
            line_id=self.sale_order.order_line.id,
            set_qty=0,
            add_qty=0,
        )
        self.assertFalse(
            self.product.product_tmpl_id.config_ok, "product is config_ok True"
        )
        self.product.product_tmpl_id.write({"config_ok": True})
        cart_update = self.sale_order._cart_update(
            product_id=product_id,
            line_id=self.sale_order.order_line.id,
            set_qty=2,
            add_qty=2,
        )
        self.assertEqual(cart_update.get("line_id"), self.sale_order.order_line.id)
        self.assertEqual(
            cart_update.get("quantity"), self.sale_order.order_line.product_uom_qty
        )

        self.sale_order.write({"order_line": False})
        self.sale_order._cart_update(
            product_id=product_id,
            set_qty=1,
            add_qty=1,
        )
        self.assertTrue(self.sale_order.order_line, "No Sale Order Line created.")

        self.sale_order._cart_update(
            product_id=product_id,
            line_id=self.sale_order.order_line.id,
            set_qty=-1,
            add_qty=1,
        )
        self.assertFalse(
            self.sale_order.order_line,
            "Order Line is exist for quantity is less than equal zero.",
        )

        self.sale_order._cart_update(
            line_id=self.sale_order.order_line.id,
            product_id=product_id,
            add_qty="test",
        )
        self.assertEqual(
            self.sale_order.order_line.product_uom_qty,
            1,
            "If wrong value is added then 1 quantity is deducted from Order Line.",
        )

        self.sale_order._cart_update(
            line_id=self.sale_order.order_line.id,
            product_id=product_id,
            set_qty="test",
        )
        self.assertEqual(
            self.sale_order.order_line.product_uom_qty,
            1,
            "If wrong value is added then Order Line quantity as it is.",
        )
