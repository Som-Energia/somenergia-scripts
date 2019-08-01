# -*- coding: utf-8 -*-
from datetime import datetime

from utils import is_company


class InvalidAccount(Exception):
    def __init__(self, message):
        super(InvalidAccount, self).__init__(message)


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
    if 'value' in vals:
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

    raise InvalidAccount(vals.get('warning', {}).get('message', ''))


def main_partner_address(O, partner_id):
    address_ids = O.ResPartnerAddress.search([
        ('partner_id.id', '=', partner_id),
        ])

    if address_ids:
        return address_ids[0]


annotation_template = u"""\
-- webforms diu: --
****Canvi de titular amb soci vinculat ({soci_name} {soci_number})****
Data de petició: {request_date}
Nou Titular: {owner_name}
NIF: {owner_nif}
Contacte: {owner_email} {owner_phone}
IBAN: {iban}
-- webforms ha dit --
"""


def update_contract_observations(O, contract_id, owner_id, member_id, bank_id, request_date):

    bank = O.ResPartnerBank.read(bank_id, ['iban'])
    member = O.SomenergiaSoci.read(member_id, ['name', 'ref']) if member_id else {}
    owner = O.ResPartner.read(owner_id, ['name', 'vat', 'address'])
    address_id = main_partner_address(O, owner_id)
    address = O.ResPartnerAddress.read(address_id, ['phone', 'mobile', 'email'])

    observations = annotation_template.format(
        soci_name=member.get('name', '-'),
        soci_number=member.get('ref', '-'),
        request_date=request_date,
        owner_name=owner['name'],
        owner_nif=owner['vat'],
        owner_email=address['email'],
        owner_phone=address['phone'] or address['mobile'],
        iban=bank['iban']
    )

    contract = O.GiscedataPolissa.read(contract_id, ['observacions'])
    O.GiscedataPolissa.write(
        [contract_id],
        dict(
            observacions=u'{new_obs}\n{old_obs}'.format(
                old_obs=contract['observacions'],
                new_obs=observations,
            )
        )
    )


def mark_contract_as_not_estimable(O, contract_id, timestamp):
    reason = u"\n(webforms)[{timestamp}] Canvi de titular".format(
        timestamp=timestamp
    )
    contract = O.GiscedataPolissa.read(contract_id)
    observations = contract['observacions_estimacio']
    observations += reason
    new_values = {
        'es_pot_estimar': False,
        'no_estimable': True,
        'observacions_estimacio': observations,
    }
    O.GiscedataPolissa.write([contract_id], new_values)
