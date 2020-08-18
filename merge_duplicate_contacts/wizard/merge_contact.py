# -*- coding: utf-8 -*-

from ast import literal_eval
import logging
import operator

# from odoo.osv import fields as old_fields
from odoo import api, fields, models
from odoo import SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError, Warning
from odoo.tools import mute_logger
import itertools

_logger = logging.getLogger('base.partner.merge')

def is_integer_list(ids):
    return all(isinstance(i, (int, long)) for i in ids)

class MergePartnerAutomatic(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    total_duplicates = fields.Integer('Total Duplicates')
    duplicate_position = fields.Integer('Duplicate Contact Position')
    associate_contact =fields.Boolean("Partner contacts associated to the contact",default=True)
    contact_not_being_customer =fields.Boolean("A contact not being customer",default=True)
    without_sales_orders =fields.Boolean("Without sales orders",default=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super(MergePartnerAutomatic, self).default_get(fields_list)
        res.update({'exclude_contact': True}) #, 'exclude_journal_item': True
        return res
        
    @api.multi
    def _action_new_next_screen(self):
        self.invalidate_cache()
        values = {}
        context = {}
        if self.line_ids:
            current_line = self.line_ids[0]
            current_partner_ids = literal_eval(current_line.aggr_ids)[-2:]
            current_partner_ids.sort()
            
            orders = self.env['sale.order'].search([('partner_id','in',current_partner_ids)], order = 'date_order desc, id desc', limit=1)
            if orders:
                first_partner_id = [orders[0].partner_id.id]
                new_current_partner_ids = list(set(current_partner_ids) - set(first_partner_id))
                current_partner_ids = first_partner_id + new_current_partner_ids
                
            values.update({
                'current_line_id': current_line.id,
                'partner_ids': [(6, 0, current_partner_ids)],
                'dst_partner_id': current_partner_ids[0],
                'state': 'selection',
            })
            self.write(values)
            
            partner1 = self.env['res.partner'].browse(current_partner_ids[0]) #self.partner_ids[0]
            partner2 = self.env['res.partner'].browse(current_partner_ids[1]) #self.partner_ids[1]
            
            partner_last_order1 = self.env['sale.order'].search([('partner_id','=',partner1.id)], order = 'date_order desc, id desc', limit=1)
            sale_order_date1 = False
            sale_order_num1 = False
            if partner_last_order1:
                sale_order_date1 = partner_last_order1.date_order
                sale_order_num1 = partner_last_order1.name
                
            partner_last_order2 = self.env['sale.order'].search([('partner_id','=',partner2.id)], order = 'date_order desc, id desc', limit=1)
            sale_order_date2 = False
            sale_order_num2 = False
            if partner_last_order2:
                sale_order_date2 = partner_last_order2.date_order
                sale_order_num2 = partner_last_order2.name

            context = {'default_last_changes_date1':partner1.write_date,
                       'default_last_changes_uid1':partner1.write_uid.id,
                       'default_last_changes_date2':partner2.write_date,
                       'default_last_changes_uid2':partner2.write_uid.id,
                       'default_last_order1':sale_order_date1,
                       'default_last_order2':sale_order_date2,
                       'default_last_order_num1':sale_order_num1,
                       'default_last_order_num2':sale_order_num2,
                       'default_partner_ids':values['partner_ids'],
                       'default_current_line_id':values['current_line_id'],
                       'default_dst_partner_id':values['dst_partner_id'],
                       'default_id1':partner1.id,
                       'default_id2':partner2.id,
                       'default_partner_id_1':partner1.id,
                       'default_partner_id_2':partner2.id,
                       'default_company_id':partner1.company_id.id,
                       'default_company_id2':partner2.company_id.id,
                       'default_name':partner1.name,
                       'default_name2':partner2.name,
                       'default_email':partner1.email,
                       'default_email2':partner2.email,
                       'default_phone':partner1.phone,
                       'default_phone2': partner2.phone,
                       'default_street': partner1.street,
                       'default_street2':partner2.street,
                       'default_street11':partner1.street2,
                       'default_street22':partner2.street2,
                       'default_zip':partner1.zip,
                       'default_zip2':partner2.zip,
                       'default_city':partner1.city,
                       'default_city2':partner2.city,
                       'default_state_id':partner1.state_id.id,
                       'default_state_id2':partner2.state_id.id,
                       'default_country_id':partner1.country_id.id,
                       'default_country_id2':partner2.country_id.id,
                       'default_is_company':partner1.is_company,
                       'default_is_company2':partner2.is_company,
                       'default_number_group':self.number_group,
                       'default_partner_wizard_id':self.id,
                       'default_state': 'selection',
                       'default_total_duplicates': self.total_duplicates,
                       'default_duplicate_position': self.duplicate_position,
                       }
            
        else:
            values.update({
                'current_line_id': False,
                'partner_ids': [],
                'state': 'finished',
            })
            
            return 
 
        return {
            'type': 'ir.actions.act_window',
            'name': 'Merge Contacts',
            'res_model': 'merge.partner.manual.check',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
    
    def _generate_query(self, fields, maximum_group=100):
        sql_fields = []
        for field in fields:
            if field in ['email', 'name']:
                sql_fields.append('lower(%s)' % field)
            elif field in ['vat']:
                sql_fields.append("replace(%s, ' ', '')" % field)
            else:
                sql_fields.append(field)

        group_fields = ', '.join(sql_fields)

        filters = []
        for field in fields:
            if field in ['email', 'name', 'vat']:
                filters.append((field, 'IS NOT', 'NULL'))

        criteria = ' AND '.join('%s %s %s' % (field, operator, value)
                                for field, operator, value in filters)

        text = [
            "SELECT min(id), array_agg(id)",
            "FROM res_partner",
        ]
        conditions = [criteria]
        if self.associate_contact:
            conditions.append("NOT EXISTS (SELECT 1 FROM res_partner as child WHERE child.parent_id = res_partner.id)")
        if self.contact_not_being_customer:
            conditions.append("customer is TRUE")
        if self.without_sales_orders:
            conditions.append("EXISTS (SELECT 1 FROM sale_order as s WHERE s.partner_id = res_partner.id)")
        
        criteria = ' AND '.join(conditions)        
        if criteria:
            text.append('WHERE %s' % criteria)
            
        text.extend([
            "GROUP BY %s" % group_fields,
            "HAVING COUNT(*) >= 2",
            "ORDER BY min(id)",
        ])

        if maximum_group:
            text.extend([
                "LIMIT %s" % maximum_group,
            ])

        return ' '.join(text)    
    
    def _process_query(self, query):
        """
        Execute the select request and write the result in this wizard
        """
        proxy = self.env['base.partner.merge.line']
        
        models = self._compute_models()
        self._cr.execute(query)

        counter = 0
        total_duplicates = 0
        for min_id, aggr_ids in self._cr.fetchall():
            if models and self._partner_use_in(aggr_ids, models):
                continue
            values = {
                'wizard_id': self.id,
                'min_id': min_id,
                'aggr_ids': aggr_ids,
            }
            # To ensure that the used partners are accessible by the user
            partners = self.env['res.partner'].search([('id', 'in', aggr_ids)])
            if len(partners) >= 2:
                ordered_partners = self._get_ordered_partner(partners.ids)
                partner_ids = [partner.id for partner in ordered_partners]
                values['aggr_ids'] = partner_ids
                proxy.create(values)
                counter += 1
                total_duplicates += len(partner_ids)-1
                
        values = {
            'state': 'selection',
            'number_group': counter,
            'total_duplicates' : total_duplicates,
            'duplicate_position': 1,
        }

        self.write(values)
        _logger.info("counter: %s", counter)
     
    @api.multi
    def action_start_manual_process(self):
        self.ensure_one()
        context = dict(self._context.copy() or {}, active_test=False)
        groups = self._compute_selected_groupby()
        query = self._generate_query(groups, self.maximum_group)
        self.with_context(context=context)._process_query(query)
        return self._action_new_next_screen()


class MergePartnerManualCheck(models.TransientModel):
    _name = 'merge.partner.manual.check'
    _description = 'Merge Partner Manual Check'
    
    
    last_changes_date1 = fields.Datetime('Last Changes')
    last_changes_date2 = fields.Datetime('Last Changes 2')
    
    last_changes_uid1 = fields.Many2one('res.users','Last Update By')
    last_changes_uid2 = fields.Many2one('res.users','Last Update By 2')
    
    last_order1 = fields.Datetime('Last Order')
    last_order2 = fields.Datetime('Last Order 2')
    
    last_order_num1 = fields.Char('Last Order Number')
    last_order_num2 = fields.Char('Last Order Number 2')
    
    id1 = fields.Char('ID 1')
    id2 = fields.Char('ID 2')
    
    partner_id_1 = fields.Many2one('res.partner','Partner')
    partner_id_2 = fields.Many2one('res.partner', 'Partner 2')
    
    company_id = fields.Many2one('res.company', 'Company')
    company_id2 = fields.Many2one('res.company', 'Company 2')
    
    name = fields.Char('Name')
    name2 = fields.Char('Name 2')
    
    email = fields.Char('Email')
    email2 = fields.Char('Email 2')
    
    phone = fields.Char('Phone')
    phone2 = fields.Char('Phone 2')
    
    street = fields.Char('Address1')
    street2 = fields.Char('Address1 2')
    
    street11 = fields.Char('Address2')
    street22 = fields.Char('Address2 2')
    
    zip = fields.Char('Zip')
    zip2 = fields.Char('Zip 2')
    
    city = fields.Char('City')
    city2 = fields.Char('City 2')
    
    state_id = fields.Many2one("res.country.state", string='State')
    state_id2 = fields.Many2one("res.country.state", string='State 2')
    
    country_id = fields.Many2one('res.country', string='Country')
    country_id2 = fields.Many2one('res.country', string='Country 2')
    
    is_company = fields.Boolean('Is Company ?')
    is_company2 = fields.Boolean('Is Company 2 ?')
    
    vat_1 = fields.Char('Vat')
    vat_2 = fields.Char('Vat 2')
    
    keep1 = fields.Boolean('Keep', default=True)
    keep2 = fields.Boolean('Keep 2')
    
    partner_wizard_id = fields.Many2one('base.partner.merge.automatic.wizard', 'Wizard')
    partner_ids = fields.Many2many('res.partner', 'partner_merge_manual_check_rel','marge_id','partner_id', string='Contacts')
    
    current_line_id = fields.Many2one('base.partner.merge.line', string='Current Line')
    dst_partner_id = fields.Many2one('res.partner', string='Destination Contact')
    
    state = fields.Selection([
        ('option', 'Option'),
        ('selection', 'Selection'),
        ('finished', 'Finished')
    ], readonly=True, required=True, string='Status', default='option')
    
    line_ids = fields.One2many('base.partner.merge.line', 'wizard_id', string='Lines')
    number_group = fields.Integer('Group of Contacts', readonly=True)
    total_duplicates = fields.Integer('Total Duplicates')
    duplicate_position = fields.Integer('Duplicate Contact Position')
    
    name_show_icon = fields.Boolean('Name Icon',compute='_compute_name_show_icon',store=True)
    email_show_icon = fields.Boolean('Email Icon',compute='_compute_email_show_icon',store=True)
    phone_show_icon = fields.Boolean('Phone Icon',compute='_compute_phone_show_icon',store=True)
    addr1_show_icon = fields.Boolean('Address1 Icon',compute='_compute_addr1_show_icon',store=True)
    addr2_show_icon = fields.Boolean('Address2 Icon',compute='_compute_addr2_show_icon',store=True)
    zip_show_icon = fields.Boolean('Zip Icon',compute='_compute_zip_show_icon',store=True)
    city_show_icon = fields.Boolean('City Icon',compute='_compute_city_show_icon',store=True)
    state_show_icon = fields.Boolean('State Icon',compute='_compute_state_show_icon',store=True)
    country_show_icon = fields.Boolean('Country Icon',compute='_compute_country_show_icon',store=True)
    vat_show_icon = fields.Boolean('Vat Icon',compute='_compute_vat_show_icon',store=True)
    is_company_show_icon = fields.Boolean('Is Company Icon',compute='_compute_is_company_show_icon',store=True)
    
    @api.multi
    @api.depends('name','name2')
    def _compute_name_show_icon(self):
        for record in self:
            if not record.name == record.name2:
                record.name_show_icon = False
            else:
                record.name_show_icon = True
    
    @api.multi
    @api.depends('email','email2')
    def _compute_email_show_icon(self):
        for record in self:
            if not record.email == record.email2:
                record.email_show_icon = False
            else:
                record.email_show_icon = True
    
    @api.multi
    @api.depends('phone','phone2')
    def _compute_phone_show_icon(self):
        for record in self:
            if not record.phone == record.phone2:
                record.phone_show_icon = False
            else:
                record.phone_show_icon = True
    
    @api.multi
    @api.depends('street','street2')
    def _compute_addr1_show_icon(self):
        for record in self:
            if not record.street == record.street2:
                record.addr1_show_icon = False
            else:
                record.addr1_show_icon = True
    
    @api.multi
    @api.depends('street11','street22')
    def _compute_addr2_show_icon(self):
        for record in self:
            if not record.street11 == record.street22:
                record.addr2_show_icon = False
            else:
                record.addr2_show_icon = True
    
    @api.multi
    @api.depends('zip','zip2')
    def _compute_zip_show_icon(self):
        for record in self:
            if not record.zip == record.zip2:
                record.zip_show_icon = False
            else:
                record.zip_show_icon = True
    
    @api.multi
    @api.depends('city','city2')
    def _compute_city_show_icon(self):
        for record in self:
            if not record.city == record.city2:
                record.city_show_icon = False
            else:
                record.city_show_icon = True
    
    @api.multi
    @api.depends('state_id','state_id2')
    def _compute_state_show_icon(self):
        for record in self:
            if not record.state_id == record.state_id2:
                record.state_show_icon = False
            else:
                record.state_show_icon = True
    
    @api.multi
    @api.depends('country_id','country_id2')
    def _compute_country_show_icon(self):
        for record in self:
            if not record.country_id == record.country_id2:
                record.country_show_icon = False
            else:
                record.country_show_icon = True
    
    @api.multi
    @api.depends('vat_1','vat_2')
    def _compute_vat_show_icon(self):
        for record in self:
            if not record.vat_1 == record.vat_2:
                record.vat_show_icon = False
            else:
                record.vat_show_icon = True
    @api.multi
    @api.depends('is_company','is_company2')
    def _compute_is_company_show_icon(self):
        for record in self:
            if not record.is_company == record.is_company2:
                record.is_company_show_icon = False
            else:
                record.is_company_show_icon = True
                
    @api.onchange('keep1')
    def _onchange_keep1(self):
        if self.keep1:
            self.keep2=False
            self.dst_partner_id = self.partner_ids and self.partner_ids[0].id or False
        
    @api.onchange('keep2')
    def _onchange_keep2(self):
        if self.keep2:
            self.keep1=False
            self.dst_partner_id = self.partner_ids and self.partner_ids[1].id or False
    
    
    @api.multi
    def action_skip(self):    
        if self.partner_wizard_id.current_line_id:
            skipped_partner_ids = self.partner_ids.ids
            new_aggr_ids = list(set(literal_eval(self.partner_wizard_id.current_line_id.aggr_ids)) - set(skipped_partner_ids))
            if not new_aggr_ids or len(new_aggr_ids)==1:
                self.partner_wizard_id.current_line_id.unlink()
            else:    
                self.partner_wizard_id.current_line_id.write({'aggr_ids': new_aggr_ids})
        else:
            raise Warning(_("No duplicates found")) #osv.except_osv(_('Error'), _("No dublicates found"))
                
        self.partner_wizard_id.write({'duplicate_position': self.partner_wizard_id.duplicate_position + 1,})
        return self.partner_wizard_id._action_new_next_screen()

    def _get_ordered_partner(self, partner_ids, context=None):
        partners = self.pool.get('res.partner').browse(list(partner_ids), context=context)
        ordered_partners = sorted(sorted(partners,
                            key=operator.attrgetter('create_date'), reverse=True),
                                key=operator.attrgetter('active'), reverse=True)
        return ordered_partners

    def _merge(self, partner_ids, dst_partner=None, context=None):
        # super-admin can be used to bypass extra checks
        extra_checks = True
        if self.env.user._is_admin():
            extra_checks = False
            
        Partner = self.env['res.partner']
        partner_ids = Partner.browse(partner_ids).exists()
        if len(partner_ids) < 2:
            return

        if len(partner_ids) > 3:
            raise UserError(_("For safety reasons, you cannot merge more than 3 contacts together. You can re-open the wizard several times if needed."))

        # check if the list of partners to merge contains child/parent relation
        child_ids = self.env['res.partner']
        for partner_id in partner_ids:
            child_ids |= Partner.search([('id', 'child_of', [partner_id.id])]) - partner_id
        if partner_ids & child_ids:
            raise UserError(_("You cannot merge a contact with one of his parent."))
        
        if len(set(partner.email for partner in partner_ids)) > 1:
            raise UserError(_("All contacts must have the same email. Only the Administrator can merge contacts with different emails."))

        # remove dst_partner from partners to merge
        if dst_partner and dst_partner in partner_ids:            
            src_partners = partner_ids - dst_partner
        else:
            ordered_partners = self._get_ordered_partner(partner_ids.ids)
            dst_partner = ordered_partners[-1]
            src_partners = ordered_partners[:-1]
        _logger.info("dst_partner: %s", dst_partner.id)
        
        if extra_checks and 'account.move.line' in self.env and self.env['account.move.line'].sudo().search([('partner_id', 'in', [partner.id for partner in src_partners])]):
            raise UserError(_("Only the destination contact may be linked to existing Journal Items. Please ask the Administrator if you need to merge several contacts linked to existing Journal Items."))

        # FIXME: is it still required to make and exception for account.move.line since accounting v9.0 ?
#         if extra_checks and 'account.move.line' in self.env and self.env['account.move.line'].sudo().search([('partner_id', 'in', [partner.id for partner in src_partners])]):
#             raise UserError(_("Only the destination contact may be linked to existing Journal Items. Please ask the Administrator if you need to merge several contacts linked to existing Journal Items."))

        # Make the company of all related users consistent
        if dst_partner.company_id:
            for user in partner_ids.mapped('user_ids'):
                user.sudo().write({'company_ids': [(6, 0, [dst_partner.company_id.id])],
                            'company_id': dst_partner.company_id.id})

        # call sub methods to do the merge
        self._update_foreign_keys(src_partners, dst_partner)
        self._update_reference_fields(src_partners, dst_partner)
        self._update_values(src_partners, dst_partner)
        
        self._log_merge_operation(src_partners, dst_partner)

        for partner in src_partners:
            if hasattr(partner, 'newsletter_sendy') and partner.newsletter_sendy:
                self._cr.execute('update res_partner set newsletter_sendy=false where id=%s'%(partner.id))
                partner.refresh()
            partner.unlink()

        # delete source partner, since they are merged
#         src_partners.unlink()
    
    @api.multi
    def _log_merge_operation(self, src_partners, dst_partner):
        _logger.info('(uid = %s) merged the partners %r with %s', self._uid, src_partners.ids, dst_partner.id)
    
    def _update_foreign_keys(self, src_partners, dst_partner, context=None):
        res = self.env['base.partner.merge.automatic.wizard']._update_foreign_keys(src_partners, dst_partner)
        return res
    
    def _update_reference_fields(self, src_partners, dst_partner, context=None):
        res = self.env['base.partner.merge.automatic.wizard']._update_reference_fields(src_partners, dst_partner)
        return res
    
    @api.model
    def _update_values(self, src_partners, dst_partner):
        _logger.debug('_update_values for dst_partner: %s for src_partners: %r', dst_partner.id, src_partners.ids)

        model_fields = dst_partner.fields_get().keys()

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item
        # get all fields that are not computed or x2many
        values = dict()
        
        form_fields = ['name','email', 'phone', 'street','street2', 'zip','city','state_id','country_id','is_company','vat']
        for column in model_fields:
            field = dst_partner._fields[column]
            if field.type not in ('many2many', 'one2many') and field.compute is None and column not in form_fields:
                for item in itertools.chain(src_partners, [dst_partner]):
                    if item[column]:
                        values[column] = write_serializer(item[column])
                        
        # remove fields that can not be updated (id and parent_id)
        values.pop('id', None)
        parent_id = values.pop('parent_id', None)
        if dst_partner.child_ids and 'is_company' not in values:
            values.update({'is_company': dst_partner.is_company})
        dst_partner.write(values)
        # try to update the parent_id
        if parent_id and parent_id != dst_partner.id:
            try:
                dst_partner.write({'parent_id': parent_id})
            except ValidationError:
                _logger.info('Skip recursive partner hierarchies for parent_id %s of partner: %s', parent_id, dst_partner.id)
    
    
    @api.multi
    def action_merge(self, context=None):
#         assert is_integer_list(ids)

        context = dict(context or {}, active_test=False)
#         this = self.browse(ids[0], context=context)
        this = self
        if this.keep1 ==False and this.keep2 == False:
            raise Warning(_("Please select a contact to keep."))
        if this.keep1:
            this.dst_partner_id = this.partner_ids and this.partner_ids[0].id or False
             
            if this.dst_partner_id:
                this.dst_partner_id.write({'company_id':this.company_id and this.company_id.id or False,
                                           'name':this.name or False,
                                           'email':this.email or False,
                                           'phone':this.phone or False,
                                           'street':this.street or False,
                                           'street2':this.street11 or False,
                                           'zip':this.zip or False,
                                           'city':this.city or False,
                                           'state_id':this.state_id and this.state_id.id or False,
                                           'country_id':this.country_id and this.country_id.id or False,
                                           'is_company':this.is_company2 or False})
                #To Avoid VAT Validation, updated it using query.
                if this.vat_1:
                    self._cr.execute("update res_partner set vat='%s' where id=%s"%(this.vat_1,this.dst_partner_id.id))
        else:
            this.dst_partner_id = this.partner_ids and this.partner_ids[1].id or False
             
            if this.dst_partner_id:
                this.dst_partner_id.write({'company_id':this.company_id2 and this.company_id2.id or False,
                                           'name':this.name2 or False,
                                           'email':this.email2 or False,
                                           'phone':this.phone2 or False,
                                           'street':this.street2 or False,
                                           'street2':this.street22 or False,
                                           'zip':this.zip2 or False,
                                           'city':this.city2 or False,
                                           'state_id':this.state_id2 and this.state_id2.id or False,
                                           'country_id':this.country_id2 and this.country_id2.id or False,
                                           'is_company':this.is_company2 or False})
                
                #To Avoid VAT Validation, updated it using query.
                if this.vat_2:
                    self._cr.execute("update res_partner set vat='%s' where id=%s"%(this.vat_2,this.dst_partner_id.id))
                    
        partner_ids = set(map(int, this.partner_ids)) #[:2]
#         custom_partner_ids = set(map(int, this.custom_partner_ids))
        if not partner_ids:
            this.write({'state': 'finished'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': this._name,
                'res_id': this.id,
                'view_mode': 'form',
                'target': 'new',
            }

        self._merge(partner_ids, this.dst_partner_id, context=context)
    
        if this.partner_wizard_id.current_line_id:
            deleted_partner_ids = list(set(partner_ids) - set([this.dst_partner_id.id]))
            new_aggr_ids = list(set(literal_eval(this.partner_wizard_id.current_line_id.aggr_ids)) - set(deleted_partner_ids))
            if not new_aggr_ids or len(new_aggr_ids)==1:
                this.partner_wizard_id.current_line_id.unlink()
            else:    
                this.partner_wizard_id.current_line_id.write({'aggr_ids': new_aggr_ids})
                    
        this.partner_wizard_id.write({'duplicate_position': this.partner_wizard_id.duplicate_position + 1,})

        return this.partner_wizard_id._action_new_next_screen()


    @api.multi
    def swap_to_left(self):
        context = self._context.get('field_name')
        if context == 'company_id2':
            self.company_id = self.company_id2            
        if context == 'name2':
            self.name = self.name2
        if context == 'email2':
            self.email = self.email2
        if context == 'phone2':
            self.phone = self.phone2
        if context == 'street2':
            self.street = self.street2
        if context == 'street22':
            self.street11 = self.street22
        if context == 'zip2':
            self.zip = self.zip2
        if context == 'city2':
            self.city = self.city2
        if context == 'state_id2':
            self.state_id = self.state_id2
        if context == 'country_id2':
            self.country_id = self.country_id2
        if context == 'is_company2':
            self.is_company = self.is_company2
        if context == 'vat_2':    
            self.vat_1 = self.vat_2
                
        return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
    
    @api.multi
    def swap_to_right(self):
        context = self._context.get('field_name')
        if context == 'company_id':
            self.company_id2 = self.company_id
        if context == 'name':
            self.name2 = self.name
        if context == 'email':
            self.email2 = self.email
        if context == 'phone':
            self.phone2 = self.phone
        if context == 'street':
            self.street2 = self.street
        if context == 'street11':
            self.street22 = self.street11
        if context == 'zip':
            self.zip2 = self.zip
        if context == 'city':
            self.city2 = self.city
        if context == 'state_id':
            self.state_id2 = self.state_id.id
        if context == 'country_id':
            self.country_id2 = self.country_id.id
        if context == 'is_company':
            self.is_company2 = self.is_company
        if context == 'vat_1':    
            self.vat_2 = self.vat_1
                
        return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

    @api.multi
    def dummy_button(self):
        return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }