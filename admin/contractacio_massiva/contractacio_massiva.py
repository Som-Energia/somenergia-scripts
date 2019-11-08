#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import csv

import requests
from consolemsg import step, success, warn, error
from yamlns import namespace as ns

import configdb


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


def crea_contractes(uri, filename):
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
            success('Status: {} \n Reason: {} \n {}', status, reason, text)


def main(csv_file, check_conn=True):

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
        else:
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
        default=False,
        const=True,
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
