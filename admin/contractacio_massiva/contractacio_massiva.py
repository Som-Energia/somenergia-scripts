# -*- coding: utf-8 -*-

import argparse
import csv

import json
import requests
import contextlib
import sys, traceback
sys.path.append('/home/david/Documents/somenergia-scripts')
from consolemsg import step, success, warn, error
from ooop_wst import OOOP_WST
from yamlns import namespace as ns

from comer.canvi_titus.models import get_or_create_partner_address
from comer.canvi_titus.utils import get_last_contract_on_cups
import configdb

def _custom_casting(data):
    power_items = ['power_p3','power_p4','power_p5','power_p6']
    data['contract_owner']['city_id'] = int(data['contract_owner']['city_id'])
    data['contract_owner']['state_id'] = int(data['contract_owner']['state_id'])
    data['cups_city_id'] = int(data['cups_city_id'])
    data['cups_state_id'] = int(data['cups_state_id'])
    if data.get('owner_is_payer').lower() == 'false':
        data['contract_payer']['city_id'] = int(data['contract_payer']['city_id'])
        data['contract_payer']['state_id'] = int(data['contract_payer']['state_id'])
    for power in power_items:
        if data[power] == '0':
            del data[power]

    return data

def _decode(o):
    if isinstance(o, str) or isinstance(o, unicode):
        try:
            if o.lower() == 'true':
                return True
            if o.lower() == 'false':
                return False
            return o

        except ValueError:
            return o
    elif isinstance(o, dict):
        return {k: _decode(v) for k, v in o.items() if v != ''}
    elif isinstance(o, list):
        return [_decode(v) for v in o]
    else:
        return o

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
        json = _decode(_custom_casting(data))
        response = requests.post(uri, json=json)
        response.raise_for_status()
        keys = [key for key in  response.json()['data']]
        if 'invalid_fields' in keys:
            raise requests.exceptions.HTTPError('invalid fields')

    except requests.exceptions.HTTPError as e:
        # check if we have invalid fields
        json_response = response.json()
        error_list = json_response.get("data", {}).get("invalid_fields", [])
        invalid_fields = [
            error.get("field") + " " + error.get("error")  for error in error_list
        ]

        if len(invalid_fields):
            msg = "Invalid fields: " + ", ".join(invalid_fields)
        else:
            msg = "An error ocurred calling Webforms API, reason: {}".format(e.message)

        raise requests.exceptions.HTTPError(msg)
    else:
        return response.status_code, response.reason, response.text

def read_contracts_data_csv(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f, delimiter=';')
        header = reader.next()

        # check if file is utf8 + BOM
        if '\xef\xbb\xbf' in header[0]:
            raise IOError

        if len(header) == 1:
            reader = csv.reader(f, delimiter=',')
            header = header[0].split(',')

        csv_content = [(dict(zip(header, row))) for row in reader if row[0]]

        for row in csv_content:
            aniuats = [item for item in row if 'contract_owner' in item]
            row['contract_owner'] = {}

            for item in aniuats:
                simple_item = item.split('contract_owner_')[1]
                row['contract_owner'][simple_item] = row[item]
                del row[item]

            aniuats = [item for item in row if 'contract_payer' in item]
            row['contract_payer'] = {}

            for item in aniuats:
                simple_item = item.split('contract_payer_')[1]
                row['contract_payer'][simple_item] = row[item]
                del row[item]

    return csv_content


def crea_contractes(uri, filename):
    O = OOOP_WST(**configdb.ooop)
    contract_petitions = read_contracts_data_csv(filename)

    for petition in contract_petitions:
        msg = "Creating contract for vat {}, soci {}, CUPS {}"
        step(msg, petition['contract_owner']['vat'], petition['member_number'], petition['cups'])
        try:
            status, reason, text = add_contract(uri, petition)
            # comprovació manual ja que sempre retorna 200 el webforms
            if len(O.GiscedataPolissa.search([('cups', '=', petition['cups'])])) == 0:
                raise requests.exceptions.HTTPError("Error en resposta del webforms")
        except requests.exceptions.HTTPError as e:
            msg = "I couldn\'t create a new contract for cups {}, reason {}"
            if 'cups exist' in e.message:
                warn(msg, petition['cups'], e)
            else:
                error(msg, petition['cups'], e)
        success("S'ha creat un nou contracte pel CUPS {}".format(petition['cups']))

def main(csv_file):

    uri = getattr(configdb, 'API_URI', False)

    if not uri:
        raise Exception("No se ha definido a qué API ataca el script")

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

    args = parser.parse_args()
    try:
        main(args.csv_file)
    except IOError as e:
        traceback.print_exc(file=sys.stdout)
        error("El formato del fichero tiene que ser UTF-8 sin BOM: {}", str(e))
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proceso no ha finalizado correctamente: {}", str(e))
    else:
        success("Script finalizado")

# vim: et ts=4 sw=4
