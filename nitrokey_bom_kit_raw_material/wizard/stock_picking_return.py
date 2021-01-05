# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    is_return_raw_materials = fields.Boolean('Return Raw Materials Instead of Finished Product.')
    show_return_raw_material = fields.Boolean("Show Return Raw Materials")

    @api.model
    def default_get(self, fields):
        res = super(ReturnPicking, self).default_get(fields)
        if 'product_return_moves' in res.keys():
            move_obj = self.env['stock.move']
            product_obj = self.env['product.product']
            bom_obj = self.env['mrp.bom']
            manufacture_route = self.env.ref('mrp.route_warehouse0_manufacture').id
            for line in res.get('product_return_moves'):
                move = move_obj.browse(line[2].get('move_id'))
                product = product_obj.browse(line[2].get('product_id'))
                product_tmpl = product.product_tmpl_id
                mrp_bom = bom_obj.search([('product_tmpl_id', '=', product_tmpl.id)], limit=1)
                product_route = product_tmpl.route_ids.ids
                if manufacture_route in product_route and mrp_bom and move and move.created_production_id:
                    res['show_return_raw_material'] = True
        return res

    def _create_returns(self):
        # Overwrite the method to create the return incoming shipment with 
        # raw material instead of the finished product based on the selected option by the user.
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                if self.is_return_raw_materials:
                    # Create the incoming shipment with raw materials.
                    product = return_line.product_id
                    product_tmpl = product.product_tmpl_id
                    mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_tmpl.id)], limit=1)
                    for bom_line in mrp_bom.bom_line_ids:
                        vals = self.get_return_raw_material_values(return_line, bom_line, new_picking)
                        r = return_line.move_id.copy(vals)
                        vals = {}
                        move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                        move_orig_to_link |= return_line.move_id
                        move_orig_to_link |= return_line.move_id\
                            .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))\
                            .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
                        move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                        move_dest_to_link |= return_line.move_id.move_orig_ids.mapped('returned_move_ids')\
                            .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))\
                            .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
                        vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
                        vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                        r.write(vals)
                else:
                    # Create the shipment with the finish good.
                    vals = self._prepare_move_default_values(return_line, new_picking)
                    r = return_line.move_id.copy(vals)
                    vals = {}

                    # +--------------------------------------------------------------------------------------------------------+
                    # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                    # |              | returned_move_ids              ↑                                  | returned_move_ids
                    # |              ↓                                | return_line.move_id              ↓
                    # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                    # +--------------------------------------------------------------------------------------------------------+
                    move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                    # link to original move
                    move_orig_to_link |= return_line.move_id
                    # link to siblings of original move, if any
                    move_orig_to_link |= return_line.move_id\
                        .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))\
                        .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))
                    move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                    # link to children of originally returned moves, if any. Note that the use of
                    # 'return_line.move_id.move_orig_ids.returned_move_ids.move_orig_ids.move_dest_ids'
                    # instead of 'return_line.move_id.move_orig_ids.move_dest_ids' prevents linking a
                    # return directly to the destination moves of its parents. However, the return of
                    # the return will be linked to the destination moves.
                    move_dest_to_link |= return_line.move_id.move_orig_ids.mapped('returned_move_ids')\
                        .mapped('move_orig_ids').filtered(lambda m: m.state not in ('cancel'))\
                        .mapped('move_dest_ids').filtered(lambda m: m.state not in ('cancel'))
                    vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link]
                    vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                    r.write(vals)
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

    def get_return_raw_material_values(self, return_line, bom_line, new_picking):
        vals = {
            'product_id': bom_line.product_id.id,
            'product_uom_qty': return_line.quantity * bom_line.product_qty,
            'product_uom': bom_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date_expected': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals
