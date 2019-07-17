# -*- coding: utf-8 -*-
from yamlns import namespace as ns

from models import (get_or_create_partner, get_or_create_partner_address,
                    get_or_create_partner_bank)


def create_fitxa_client(
        O,
        full_name, vat, lang, email, phone,
        street, postal_code, city_id, state_id, country_id,
        iban, become_member=False):

    partner_id, partner_created = get_or_create_partner(
        O, full_name, vat, lang, become_member
    )
    address_id, _ = get_or_create_partner_address(
        O, partner_id, street, postal_code, city_id, state_id, country_id, email, phone
    )
    bank_id = get_or_create_partner_bank(O, partner_id, iban, country_id)

    partner_data = ns(O.ResPartner.read(partner_id))
    address_data = ns(O.ResPartnerAddress.read(address_id))

    return ns(dict(
        client_id=partner_data.id,
        existent=not partner_created,
        name=partner_data.name,
        vat=partner_data.vat,
        address=address_data.street,
        bank_id=bank_id,
    ))
