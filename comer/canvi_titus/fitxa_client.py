# -*- coding: utf-8 -*-
import argparse
import json
import xmlrpclib
from datetime import datetime

from consolemsg import error, step, success, warn
from yamlns import namespace as ns

import configdb
from models import (create_m1_changeowner_case, get_or_create_partner,
                    get_or_create_partner_address, get_or_create_partner_bank,
                    mark_contract_as_not_estimable,
                    update_contract_observations)
from ooop_wst import OOOP_WST
from utils import (get_contract_info, get_cups_address,
                   get_last_contract_on_cups, get_memberid_by_partner,
                   read_canvi_titus_csv, sanitize_date, sanitize_iban,
                   transaction)

LANG_TABLE = {
    'CAT': 'ca_ES',
    'CAST': 'es_ES'
}


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
        address_id=address_id,
        bank_id=bank_id,
    ))


def update_old_contract_information(
        O,
        contract_number, cups, new_owner_id, member_id, new_bank_id, request_date):

    contract_id = O.GiscedataPolissa.search([('name', 'ilike', contract_number)])
    if not contract_id:
        raise Exception("Contract {} not found".format(contract_number))

    assert len(contract_id) <= 1, "More than one contract, I don't now what to do :("

    contract_info = O.GiscedataPolissa.read(contract_id, ['cups'])[0]
    msg = "Contract has diferent cups {} =/= {}"
    assert cups == contract_info['cups'][1], msg.format(cups, contract_info['cups'][1])

    update_contract_observations(
        O,
        contract_id=contract_id[0],
        owner_id=new_owner_id,
        member_id=member_id,
        bank_id=new_bank_id,
        request_date=request_date
    )
    mark_contract_as_not_estimable(O, contract_id[0], str(datetime.now()))


def create_m1_chageowner(
        O,
        contract_number, cups,
        new_owner_vat, new_owner_id, old_owner_id, member_id, address_id,
        notification_address_id, bank_id, signature_date, cnae_id,
        owner_change_type, lang, other_payer):

    contract_id = O.GiscedataPolissa.search([('name', 'ilike', contract_number)])
    if not contract_id:
        raise Exception("Contract {} not found".format(contract_number))

    assert len(contract_id) <= 1, "More than one contract, I don't now what to do :("

    contract_info = O.GiscedataPolissa.read(contract_id, ['cups'])[0]
    msg = "Contract has diferent cups {} =/= {}"
    assert cups == contract_info['cups'][1], msg.format(cups, contract_info['cups'][1])

    res = create_m1_changeowner_case(
        t=O,
        contract_id=contract_id[0],
        new_owner_vat=new_owner_vat,
        new_owner_id=new_owner_id,
        old_owner_id=old_owner_id,
        member_id=member_id,
        address_id=address_id,
        notification_address_id=notification_address_id,
        bank_id=bank_id,
        signature_date=signature_date,
        cnae_id=cnae_id,
        owner_change_type=owner_change_type,
        lang=lang,
        other_payer=other_payer
    )
    if 'ERROR' in res[1].upper():
        raise Exception(res[1])

    success(res[1])
    return res


def canvi_titus(O, new_owners):

    for new_client in new_owners:
        try:
            cups = new_client.get('CUPS', '').strip().upper()

            msg = "Creating new profile of {}, dni: {}"
            step(msg.format(new_client['Nom nou titu'], new_client['DNI'].strip().upper()))

            msg = "Getting address information of cups {}"
            step(msg.format(cups))

            cups_address = get_cups_address(O, cups)
            contract_info = get_contract_info(
                O, new_client.get('Contracte', '')
            )
            old_owner_vat = O.ResPartner.read(contract_info.titular[0], ['vat'])['vat']

            with transaction(O) as t:
                profile_data = create_fitxa_client(
                    t,
                    full_name=new_client['Nom nou titu'].strip(),
                    vat='ES{}'.format(new_client['DNI'].strip().upper()),
                    lang=LANG_TABLE.get(new_client['Idioma'].strip().upper(), 'es_ES'),
                    email=new_client['Mail'].strip(),
                    phone=new_client['Tlf'].strip(),
                    street=cups_address['street'],
                    postal_code=cups_address['dp'] or '',
                    city_id=cups_address['id_municipi'],
                    state_id=cups_address['id_state'],
                    country_id=cups_address['id_country'],
                    iban=sanitize_iban(new_client['IBAN'])
                )
                member_id = get_memberid_by_partner(t, profile_data.client_id)

                msg = "Creating change owner M1(T) atr case {} -> {}"
                step(msg.format(old_owner_vat, new_client['DNI'].strip().upper()))

                changeowner_res = create_m1_chageowner(
                    t,
                    contract_number=new_client['Contracte'],
                    cups=cups,
                    new_owner_vat='ES{}'.format(new_client['DNI'].strip().upper()),
                    new_owner_id=profile_data.client_id,
                    old_owner_id=contract_info.titular,
                    member_id=member_id,
                    address_id=profile_data.address_id,
                    notification_address_id=profile_data.address_id,
                    bank_id=profile_data.bank_id,
                    signature_date=sanitize_date(new_client['Data']),
                    cnae_id=contract_info.cnae[0],
                    owner_change_type='T',
                    lang=LANG_TABLE.get(new_client['Idioma'].strip().upper(), 'es_ES'),
                    other_payer=False
                )

                msg = "Setting as not 'estimable' and updating observations "\
                      "to contract: {}"
                step(msg.format(new_client['Contracte']))
                update_old_contract_information(
                    t,
                    contract_number=new_client['Contracte'],
                    cups=cups,
                    new_owner_id=profile_data.client_id,
                    new_bank_id=profile_data.bank_id,
                    member_id=member_id,
                    request_date=new_client['Data']
                )
        except xmlrpclib.Fault as e:
            msg = "An error ocurred creating {}, dni: {}, contract: {}. Reason: {}"
            error(msg.format(
                new_client['Nom nou titu'], new_client['DNI'], new_client['Contracte'], e.faultString.split('\n')[-2]
            ))
        except Exception as e:
            msg = "An error ocurred creating {}, dni: {}, contract: {}. Reason: {}"
            error(msg.format(
                new_client['Nom nou titu'], new_client['DNI'], new_client['Contracte'], e.message.encode('utf8')
            ))
        else:
            result = profile_data.deepcopy()
            contract_id = get_last_contract_on_cups(O, cups)

            result['case_id'] = changeowner_res[2]
            result['new_contract_id'] = contract_id
            result['cups'] = cups
            msg = "M1 ATR case successful created with data:\n {}"
            success(msg.format(json.dumps(result, indent=4, sort_keys=True)))


def main(csv_file, check_conn=True):
    O = OOOP_WST(**configdb.ooop)

    if check_conn:
        msg = "You are connected to: {}, do you want to continue? (Y/n)"
        step(msg.format(O.uri))
        answer = raw_input()
        while answer.lower() not in ['y', 'n', '']:
            answer = raw_input()
            step("Do you want to continue? (Y/n)")
        if answer in ['n', 'N']:
            raise KeyboardInterrupt

    csv_content = read_canvi_titus_csv(csv_file)

    canvi_titus(O, csv_content)

    step("Closing connection with ERP")
    O.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatische Kunde Profile erstellen'
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        required=True,
        help="csv amb les noves fitxes cliente a crear"
    )

    parser.add_argument(
        '--check-conn',
        type=bool,
        nargs='?',
        default=False,
        const=True,
        help="Check para comprobar a que servidor nos estamos conectando"
    )

    args = parser.parse_args()
    try:
        main(args.csv_file, args.check_conn)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    else:
        success("Chao!")
