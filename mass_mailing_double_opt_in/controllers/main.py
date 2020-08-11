# -*- coding: utf-8 -*-
import uuid

from odoo.http import route, request, Controller
from odoo.addons.mass_mailing.controllers.main import MassMailController


class MassMailController(MassMailController):

    @route('/website_mass_mailing/subscribe', type='json', website=True, auth="public")
    def subscribe(self, list_id, email, **post):
        Contacts = request.env['mail.mass_mailing.contact'].sudo()
        name, email = Contacts.get_name_email(email)

        # inline add_to_list as we've already called half of it
        existing_contact = Contacts.search([
            ('list_ids', 'in', [int(list_id)]),
            ('email', '=', email),
        ], limit=1)
        if existing_contact:
            existing_list_contact = existing_contact.subscription_list_ids.filtered(lambda c: c.list_id.id == int(list_id))
            if existing_list_contact.opt_out:
                mailing_list_contact = existing_list_contact
        else:
            mailing_contact = Contacts.create({'name': name, 'email': email, 'opt_out': True, 'list_ids': [(6,0,[int(list_id)])]})
            mailing_list_contact = mailing_contact.subscription_list_ids.filtered(lambda c: c.list_id.id == int(list_id))
        if mailing_list_contact:
            mailing_list_contact.write({
                'opt_out': True,
                'access_token': str(uuid.uuid4().hex),
            })
            template = request.env.ref("mass_mailing_double_opt_in.newsletter_confirmation_request_template").sudo()
            template.send_mail(mailing_list_contact.id, force_send=True)

        # add email to session
        request.session['mass_mailing_email'] = email
        return True


class ConsentController(Controller):
    @route("/newsletter/confirmation/<access_token>",
           type="http", auth="none", website=True)
    def consent(self, access_token, **kwargs):
        mailing_list_contact = request.env['mail.mass_mailing.list_contact_rel'].sudo().search([('access_token', '=', access_token)])
        if mailing_list_contact:
            mailing_list_contact.write({'opt_out': False})
            template = request.env.ref("mass_mailing_double_opt_in.newsletter_confirmation_success_template").sudo()
            template.send_mail(mailing_list_contact.id, force_send=True)
            return request.redirect("https://www.nitrokey.com/subscribed")
