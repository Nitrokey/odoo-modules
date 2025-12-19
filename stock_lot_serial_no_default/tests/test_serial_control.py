from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockLotSerialNoDefault(TransactionCase):
    """Test that serial numbers are not automatically assigned during reservation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create locations
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

        # Create a product tracked by serial number
        cls.product_serial = cls.env["product.product"].create(
            {
                "name": "Test Product Serial",
                "type": "consu",
                "is_storable": True,
                "tracking": "serial",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

        # Create a product tracked by lot
        cls.product_lot = cls.env["product.product"].create(
            {
                "name": "Test Product Lot",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

        # Create a product without tracking
        cls.product_none = cls.env["product.product"].create(
            {
                "name": "Test Product No Tracking",
                "type": "consu",
                "is_storable": True,
                "tracking": "none",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

        # Create serial numbers for the serial-tracked product
        cls.serial_1 = cls.env["stock.lot"].create(
            {
                "name": "SERIAL-001",
                "product_id": cls.product_serial.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.serial_2 = cls.env["stock.lot"].create(
            {
                "name": "SERIAL-002",
                "product_id": cls.product_serial.id,
                "company_id": cls.env.company.id,
            }
        )

        # Create lot for the lot-tracked product
        cls.lot_1 = cls.env["stock.lot"].create(
            {
                "name": "LOT-001",
                "product_id": cls.product_lot.id,
                "company_id": cls.env.company.id,
            }
        )

        # Add stock for all products
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_serial,
            cls.stock_location,
            1.0,
            lot_id=cls.serial_1,
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_serial,
            cls.stock_location,
            1.0,
            lot_id=cls.serial_2,
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_lot,
            cls.stock_location,
            10.0,
            lot_id=cls.lot_1,
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_none,
            cls.stock_location,
            100.0,
        )

    def test_serial_no_automatic_assignment(self):
        """Test that serial numbers are NOT automatically assigned."""
        # Create a picking for serial-tracked product
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )

        # Create a move for 1 unit of serial-tracked product
        move = self.env["stock.move"].create(
            {
                "name": "Test Move Serial",
                "product_id": self.product_serial.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_serial.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        # Confirm the picking
        picking.action_confirm()

        # Reserve stock (this is where automatic assignment would happen)
        picking.action_assign()

        # Verify the move is assigned (reserved)
        self.assertEqual(
            move.state,
            "assigned",
            "Move should be in assigned state after reservation",
        )

        # CRITICAL TEST: Verify that move lines exist but have NO lot_id
        self.assertTrue(
            move.move_line_ids,
            "Move lines should be created after reservation",
        )
        for move_line in move.move_line_ids:
            self.assertFalse(
                move_line.lot_id,
                "Serial number should NOT be automatically assigned to move line",
            )
            self.assertEqual(
                move_line.quantity,
                1.0,
                "Reserved quantity should be 1.0 even without lot_id assignment",
            )

    def test_lot_tracking_still_works(self):
        """Test that lot-tracked products still get automatic assignment."""
        # Create a picking for lot-tracked product
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )

        # Create a move for lot-tracked product
        move = self.env["stock.move"].create(
            {
                "name": "Test Move Lot",
                "product_id": self.product_lot.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product_lot.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        # Confirm and reserve
        picking.action_confirm()
        picking.action_assign()

        # Verify lot-tracked products still get automatic assignment
        self.assertEqual(move.state, "assigned")
        self.assertTrue(move.move_line_ids)
        # For lot tracking, the lot_id should still be assigned
        lot_assigned = any(ml.lot_id for ml in move.move_line_ids)
        self.assertTrue(
            lot_assigned,
            "Lot-tracked products should still get automatic lot assignment",
        )

    def test_no_tracking_still_works(self):
        """Test that products without tracking still work normally."""
        # Create a picking for non-tracked product
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )

        # Create a move
        move = self.env["stock.move"].create(
            {
                "name": "Test Move No Tracking",
                "product_id": self.product_none.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product_none.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        # Confirm and reserve
        picking.action_confirm()
        picking.action_assign()

        # Verify normal reservation works
        self.assertEqual(move.state, "assigned")
        self.assertTrue(move.move_line_ids)
        self.assertEqual(
            sum(move.move_line_ids.mapped("quantity")),
            10.0,
            "Full quantity should be reserved for non-tracked products",
        )

    def test_manual_serial_entry_still_possible(self):
        """Test that staff can manually enter serial numbers after reservation."""
        # Create and reserve a picking
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )

        move = self.env["stock.move"].create(
            {
                "name": "Test Move Serial Manual",
                "product_id": self.product_serial.id,
                "product_uom_qty": 1.0,
                "product_uom": self.product_serial.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )

        picking.action_confirm()
        picking.action_assign()

        # Manually assign a serial number to a move line
        move_line = move.move_line_ids[0]
        move_line.write(
            {
                "lot_id": self.serial_1.id,
                "quantity": 1.0,
            }
        )

        # Verify manual assignment works
        self.assertEqual(
            move_line.lot_id.id,
            self.serial_1.id,
            "Manual serial number assignment should work",
        )
        self.assertEqual(
            move_line.quantity,
            1.0,
            "Manual quantity assignment should work",
        )

        # Verify picking can be validated with manual serial entry
        picking.button_validate()
        self.assertEqual(
            picking.state,
            "done",
            "Picking should be completed after manual serial entry",
        )
