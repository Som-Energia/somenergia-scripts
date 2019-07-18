# -*- coding: utf-8 -*-
import argparse
import csv
from io import open

from consolemsg import error, step, success, warn
from yamlns import namespace as ns

import configdb
from models import (get_or_create_partner, get_or_create_partner_address,
                    get_or_create_partner_bank)
from ooop_wst import OOOP_WST
from utils import transaction


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


def get_cups_address(O, cups):
    try:
        cups_address_data = O.GiscedataCupsPs.read(
            O.GiscedataCupsPs.search([('name', '=', cups)])[0],
            ['direccio', 'dp', 'id_municipi']
        )
        id_municipi = cups_address_data['id_municipi'][0]
        cups_address_data['id_municipi'] = id_municipi

        id_state = O.ResMunicipi.read(id_municipi, ['state'])['state'][0]
        cups_address_data['id_state'] = id_state

        id_country = O.ResCountryState.read(id_state, ['country_id'])['country_id'][0]
        cups_address_data['id_country'] = id_country

    except IndexError:
        cups_address_data = {}
    else:
        cups_address_data['street'] = cups_address_data['direccio']
        del cups_address_data['direccio']
        del cups_address_data['id']

    return ns(cups_address_data)


def read_canvi_titus_csv(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        header = reader.next()
        csv_content = [dict(zip(header, row)) for row in reader if row[0]]

    return csv_content


def main(csv_file, check_conn=True):
    O = OOOP_WST(configdb.ooop)

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

    for new_client in csv_content:
        try:
            cups_address = get_cups_address(
                O, new_client.get('CUPS', None)
            )
            with transaction(O) as t:
                profile_data = create_fitxa_client(
                    t,
                    full_name=new_client['Nom nou titu'],
                    vat=new_client['DNI'],
                    lang=new_client['Idioma'],
                    email=new_client['Mail'],
                    phone=new_client['Tlf'],
                    street=cups_address['street'],
                    postal_code=cups_address['postal_code'],
                    city_id=cups_address['municipi_id'],
                    state_id=cups_address['state_id'],
                    country_id=cups_address['country_id'],
                    iban=new_client['IBAN']
                )
        except Exception as e:
            msg = "An error ocurred creating {}, dni: {}, contract:{}. Reason: {}"
            error(msg.format(
                new_client['Nom nou titu'], new_client['DNI'], new_client['Contracte'], str(e)
            ))
        else:
            msg = "Profile successful created with data: \n {}"
            success(msg.format(profile_data))

    step("Closing connection with ERP")
    O.close()


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            description='Automatische Kunde Profile erstellen'
        )

        parser.add_argument(
            '--file',
            type=file,
            dest='csv_file',
            help="csv amb les noves fitxes cliente a crear"
        )

        parser.add_argument(
            '--check-conn',
            type=bool,
            default=False,
            help="Check para comprobar a que servidor nos estamos conectando"
        )

        args = parser.parse_args()

        main(args.csv_file, args.check_conn)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    else:
        success("Chao!")
