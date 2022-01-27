from odoo import models
from odoo.exceptions import ValidationError


class MRPProduction(models.Model):
    _inherit = 'mrp.production'

    def return_active_id(self, product, quantity):
        product = self.env['product.product'].browse(product)
        picking_type_id = self._get_default_picking_type()
        picking_type = self.env['stock.picking.type'].browse(picking_type_id)
        location_id = self._get_default_location_src_id()
        location_dest_id = self._get_default_location_dest_id()
        bom = self.env['mrp.bom']._bom_find(product=product, picking_type=picking_type, company_id=self.company_id.id)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action = self.env['ir.model.data'].xmlid_to_object('mrp.mrp_production_action')
        if product and bom:
            vals = {'product_id': product.id,
                    'product_qty': quantity,
                    'product_uom_id': product.uom_id.id,
                    'location_dest_id': location_dest_id,
                    'location_src_id': location_id,
                    'picking_type_id': picking_type_id,
                    'bom_id': bom.id,
                    }
            mrp_production = self.create(vals)
            return base_url + '/web#id=%s&action=%s&model=mrp.production&view_type=form' % (mrp_production.id, action.id)
        raise ValidationError("Product does not found!!")

    def product_config_wizard(self):
        form_view = self.env.ref('sale.sale_product_configurator_view_form')
        return {
            'name': 'Configure a product',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.product.configurator',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(form_view.id, 'form')],
            'target': 'new',
            'context': {'config_product': True},
        }

