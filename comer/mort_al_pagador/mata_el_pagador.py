#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from yamlns import namespace as ns
from consolemsg import step, success, error, warn
import csv
import argparse

O = None
doit = False


def connect_erp():
    global O
    if O:
        return O
    step("Connectant a l'erp")
    O = Client(**configdb.erppeek)
    step("connectat...")
    return O


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="modifica els contractes eliminant la figura del pagador"
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        required=True,
        help="csv amb les polisses a modificar"
    )

    parser.add_argument(
        '--doit',
        type=bool,
        default=False,
        const=True,
        nargs='?',
        help='realitza les accions'
    )

    args = parser.parse_args()
    if args.doit:
        success("Es faran canvis a les polisses (--doit)")
    else:
        success("No es faran canvis a les polisses (sense opció --doit)")
    global doit
    doit = args.doit

    return args


def read_data_from_csv(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f, delimiter=';')
        header = reader.next()

        # check if file is utf8 + BOM
        if '\xef\xbb\xbf' in header[0]:
            raise IOError

        if len(header) == 1:
            reader = csv.reader(f, delimiter=',')
            header = header[0].split(',')

        csv_content = [ns(dict(zip(header, row))) for row in reader if row[0]]

    return csv_content


def get_polissa_ids_from_csv(filename):
    pol_ids = []
    for contract_name in read_data_from_csv(filename):
        pol_obj = O.GiscedataPolissa
        pol_id = pol_obj.search([('name', '=', contract_name.contracte)])
        if len(pol_id) > 1:
            warn("Multiples resultats per polissa {} : {}",
                 contract_name.contracte, pol_id)
        elif len(pol_id) == 0:
            warn("Sense resultats per polissa {}", contract_name.contracte)
        else:
            pol_ids.extend(pol_id)
    return pol_ids


def kill_pagador(pol_ids):
    pol_obj = O.GiscedataPolissa
    partner_obj = O.ResPartner

    for pol_id in pol_ids:
        pol_vals = pol_obj.read(pol_id, ['titular', 'pagador', 'name'])

        num_pol = pol_vals['name']
        titular_id = pol_vals['titular'][0]
        pagador_id = pol_vals['pagador'][0]

        if titular_id == pagador_id:
            warn("El titular i el pagador de la pòlissa són iguals per " + \
                 "la pòlissa {}".format(num_pol))
            continue

        try:
            titular_address_id = partner_obj.address_get(titular_id)['default']
            pol_obj.write(pol_id, {'pagador_sel': 'altre_p', 'pagador': titular_id, 
                'direccio_pagament': titular_address_id})
            success("Pòlissa {} modificada correctament".format(num_pol))
        except Exception as e:
            error("Error al escriure els canvis per la pòlissa {}: {}".format(num_pol, str(e)))


if __name__ == '__main__':
    args = parse_arguments()
    O = connect_erp()

    pol_ids = get_polissa_ids_from_csv(args.csv_file)
    success("Extrets {} id's de polisses del csv", len(pol_ids))
    kill_pagador(pol_ids)
    success("Script finalitzat")


# vim: et ts=4 sw=4
