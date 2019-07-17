# -*- coding: utf-8 -*-
from datetime import datetime

from utils import is_company


def get_or_create_partner(t, name, vat, lang, become_member, proxy_name=None, proxy_vat=None):
    '''
        t: erp_peek instance
        name: full name or company of the partner
        vat: vat number
        lang: language of the partner
        become_member: True if the new partner will be a member of som
        proxy_name: Name of the proxy if partner is a company
        proxy_vat: Vat number of the proxy if partner is a company
        returns partner id and if the partner is created or not
    '''
    now = datetime.now()
    c_soci = t.ResPartnerCategory.search([('name', '=', 'Soci')])
    partner_model = 'res.partner.soci' if become_member else 'res.partner.titular'
    comment = u" Persona representant: {}\n" \
              u" NIF representant: {}".format(proxy_name, proxy_vat) \
              if is_company(vat[2:]) else u""

    owner_ids = t.ResPartner.search([('vat', '=', vat)])
    if not owner_ids:
        partner_vals = {
            'name': name,
            'vat': vat,
            'ref': t.IrSequence.get_next(partner_model),
            'active': True,
            'lang': lang,
            'comment': comment,
            'comercial': 'webforms',
            'date': now.strftime('%Y-%m-%d'),
            'customer': True
        }
        if become_member:
            partner_vals.update({'category_id': [(6, 0, c_soci)]})
        owner_id = t.ResPartner.create(partner_vals)
        return owner_id, True

    return owner_ids[0], False


def get_or_create_poblacio(t, id_municipi):
    """
        Retrieves the poblacio with the same name as
        the municipi with id `id_municipi`.
        If it does not exist yet, it creates it.
    """
    municipi = t.ResMunicipi.read(id_municipi, ['name'])
    if not municipi: return None

    poblacio_ids = t.ResPoblacio.search([
        ('municipi_id', '=', municipi['id']),
        ('name', '=', municipi['name']),
        ])
    if poblacio_ids:
        return poblacio_ids[0]

    poblacio_id = t.ResPoblacio.create(dict(
        name=municipi['name'],
        municipi_id=municipi['id'],
    ))  # , context) # TODO: review if context is usefut at all

    return poblacio_id


def get_or_create_partner_address(
        t, partner_id,
        street, postal_code, city_id, state_id, country_id,
        email, phone, mobile=None):

    '''
        t: erp_peek instance
        partnerid: ID of the partner to asociate or get the  address
        street: full name of the street. name, number, flat number, door..
        postal_code: postal code of the city
        city_id: id of the city (this is not ine code!!)
        state_id: id of the state
        country: id of the country
        email: email for notifications
        phone: principal phone of contact
        mobile: second phone of contact
        returns res_partner_address id and if the address is created or not
    '''

    partner_address_ids = t.ResPartnerAddress.search([
        ('street', '=', street),
        ('partner_id.id', '=', partner_id)
    ])

    if not partner_address_ids:
        name = t.ResPartner.read(partner_id, ['name'])['name']
        town_id = get_or_create_poblacio(t, city_id)
        partner_address_vals = {
            'partner_id': partner_id,
            'name': name,
            'phone': phone,
            'email': email,
            'nv': street,
            'zip': postal_code,
            'id_poblacio': town_id,
            'id_municipi': city_id,
            'state_id': state_id,
            'country_id': country_id
        }
        if mobile is not None:
            partner_address_vals.update(mobile=mobile)

        partner_address_id = t.ResPartnerAddress.create(partner_address_vals)
        return partner_address_id, True

    return partner_address_ids[0], False


def get_or_create_partner_bank(t, partner_id, iban, country_id, state_id=False):
    """
    If such an iban is alredy a bank account for the
    partner, it returns it.
    If not it creates it and returns the new one.
    """
    bank_ids = t.ResPartnerBank.search([
        ('iban', '=', iban),
        ('partner_id', '=', partner_id),
        ])
    if bank_ids: return bank_ids[0]
    vals = t.ResPartnerBank.onchange_banco(
        [], iban[4:], country_id, {})
    vals = vals['value']
    vals.update({
        'name': '',
        'state': 'iban',
        'iban': iban,
        'partner_id': partner_id,
        'country_id': country_id,
        'acc_country_id': country_id,
        'state_id': state_id,
    })
    return t.ResPartnerBank.create(vals)
