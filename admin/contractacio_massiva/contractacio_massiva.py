#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import csv

import requests
from consolemsg import step, success, warn, error
from ooop_wst import OOOP_WST
from yamlns import namespace as ns

from comer.canvi_titus.models import get_or_create_partner_address
from comer.canvi_titus.utils import get_last_contract_on_cups
import configdb

@contextlib.contextmanager
def transaction(O):
    t = O.begin()
    try:
        yield t
    except:
        t.rollback()
        raise
    else:
        t.commit()
    finally:
        t.close()
        del t

def add_contract(uri, data):
    try:
        response = requests.post(uri, data=data)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        msg = "An error ocurred calling Webforms API, reason: {}"
        warn(msg, e.message)
        raise e
    else:
        return response.status_code, response.reason, response.text


def read_contracts_data_csv(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f, delimiter=';')
        header = reader.next()
        if len(header) == 1:
            reader = csv.reader(f, delimiter=',')
            header = header[0].split(',')

        csv_content = [ns(dict(zip(header, row))) for row in reader if row[0]]

    return csv_content


def create_contract_address(O, cups, contact_email):
    contract_id = get_last_contract_on_cups(O, cups)

    _, partner_id = O.GiscedataPolissa.read(contract_id, ['titular'])['titular']

    new_parner_address_id, created = get_or_create_partner_address(
        O,
        partner_id=partner_id,
        street='',
        postal_code='',
        city_id='',
        state_id='',
        country_id='',
        email=contact_email,
        phone=''
    )

    O.GiscedataPolissa.write(
        contract_id,
        values={
            'notificacio': 'altre_p',
            'direccio_notificacio': new_parner_address_id,
            'altre_p': partner_id
        }
    )

def crea_contractes(uri, filename):
    O = OOOP_WST(**configdb.ooop)
    contract_petitions = read_contracts_data_csv(filename)

    for petition in contract_petitions:
        if getattr(configdb, 'TESTING', False):
            petition.id_soci = configdb.personaldata['nsoci']
            petition.dni = configdb.personaldata['nif']
            petition.soci_titular = 0
        msg = "Creating contract for vat {}, soci {}, CUPS {}"
        step(msg, petition.dni, petition.id_soci, petition.cups)
        try:
            status, reason, text = add_contract(uri, petition)
        except requests.exceptions.HTTPError as e:
            msg = "I couldn\'t create a new contract for cups {}, reason {}"
            error(msg, petition.cups, e)
        else:
            try:
                with transaction(O) as t:
                    create_contact_address(t, petition.cups, petition.notifiacion_email)
            except Exception as e:
                msg = "An uncontroled exception ocurred, reason: %s"
                error(msg, str(e))
            else:
                success('Status: {} \n Reason: {} \n {}', status, reason, text)


def main(csv_file, check_conn=False):

    uri = getattr(configdb, 'API_URI', False)

    if not uri:
        raise KeyboardInterrupt("No URI, no money")
    if check_conn:
        msg = "You are requesting to: {}, do you want to continue? (Y/n)"
        step(msg.format(uri))
        answer = raw_input()
        while answer.lower() not in ['y', 'n', '']:
            answer = raw_input()
            step("Do you want to continue? (Y/n)")

        if answer in ['n', 'N']:
            raise KeyboardInterrupt
    
    crea_contractes(uri, csv_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Erstellen Sie Verträge in loser Schüttung'
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
        dest='check_conn',
        default=False,
        help="Check para comprobar que URL queremos atacar"
    )

    args = parser.parse_args()
    print("Check conn: ", args.check_conn)
    try:
        main(args.csv_file, args.check_conn)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    except IndexError:
        warn("No se interprear lo que me dices, sorry :'(")
    except Exception as e:
        warn("Ka pachao?: {}", str(e))
    else:
        success("Chao!")
