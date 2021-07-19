#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import csv

import requests
import contextlib
import sys, traceback
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
            fields = [item for item in row if 'contract_owner' in item]
            row['contract_owner'] = {}

            for item in fields:
                row['contract_owner'][item] = row[item]
                del row[item]

    return csv_content


def create_contact_address(O, petition):
    contract_id = None
    try:
        contract_id = get_last_contract_on_cups(O, petition.cups)
    except:
        error = "This cups did not have any previous contract in somenergia"
        raise Exception(error)

    partner_id, _ = O.GiscedataPolissa.read(contract_id, ['titular'])['titular']

    country_id = O.ResCountry.search([('code','like','ES')])[0]
    new_partner_address_id, created  = get_or_create_partner_address(
        O,
        partner_id=partner_id,
        street='Adreça electronica - ' + petition.compte_email,
        postal_code=petition.titular_cp,
        city_id=int(petition.titular_municipi),
        state_id=petition.titular_provincia,
        country_id=country_id,
        email=petition.compte_email,
        phone=''
    )

    values={
        'notificacio': 'titular',
        'direccio_notificacio': new_partner_address_id,
        'titular': partner_id
    }
    O.GiscedataPolissa.write(
        contract_id, values
    )
    return O.GiscedataPolissa.read(contract_id, ['name'])['name']

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
            # comprovació manual ja que sempre retorna 200 el webforms
            if len(O.GiscedataPolissa.search([('cups', '=', petition.cups)])) == 0:
                raise requests.exceptions.HTTPError("Error en resposta del webforms")
        except requests.exceptions.HTTPError as e:
            msg = "I couldn\'t create a new contract for cups {}, reason {}"
            if 'cups exist' in e.message:
                warn(msg, petition.cups, e)
            else:
                error(msg, petition.cups, e)
        else:
            try:
                with transaction(O) as t:
                    contracte = create_contact_address(O, petition)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                msg = "An uncontroled exception ocurred, reason: {}"
                error(msg, str(e))
            else:
                success("S'ha creat un nou contracte amb numero: {} pel CUPS {}".format(contracte, petition.cups))

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
