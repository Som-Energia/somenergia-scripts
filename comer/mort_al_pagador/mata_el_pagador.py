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


if __name__ == '__main__':
    args = parse_arguments()
    O = connect_erp()

    pol_ids = get_polissa_ids_from_csv(args.csv_file)


# vim: et ts=4 sw=4
