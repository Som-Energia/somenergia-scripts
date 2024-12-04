#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import traceback
from erppeek import Client
import configdb
import argparse
import sys
import csv
from consolemsg import error, step, success, warn
from tqdm import tqdm
from datetime import datetime, timedelta


STATES_GESTIO_DESCOMPTES = [
    ('no_aplicar', 'No aplicar descomptes'),
    ('aplicar', 'Aplicar descomptes disponibles'),
    ('min_import', "Aplicar descomptes a partir d'un import mínim"),
    ('hivern', "Aplicar descomptes els mesos de Novembre, Desembre, Gener, Febrer i Març"),
    ('aplicar_tot', "Aplicar tot l'import de la bateria"),
    ('remesar', 'Remesar'),
]


step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
pol_obj = O.GiscedataPolissa


def modify_solar_flux(pol_id, state, doit):
    p = pol_obj.browse(pol_id)
    if not p.bateria_activa or len(p.bateria_ids) == 0:
        return False

    if doit:
        b = p.bateria_ids[0]
        b.gestio_descomptes = state
    return True


def search_and_add(pol_name):
    pol_name = pol_name.strip().zfill(7)
    step("Cerquem la polissa... {}", pol_name)
    found_ids = pol_obj.search(
        [('name', '=', pol_name)],
        context={'active_test': False}
    )

    if len(found_ids) != 1:
        warn("item {} ha trobat {} polisses! {}", pol_name, len(found_ids), found_ids)
        return []

    return found_ids


def search_polisses_by_name(pol_names):
    pol_ids = []
    pol_names_list = pol_names.split(',')
    step("Trobades {} noms de possibles pòlisses", len(pol_names_list))
    for pol_name in pol_names_list:
        pol_ids.extend(search_and_add(pol_name))

    step("Trobades {} pòlisses", len(pol_ids))
    return pol_ids


def search_polisses_by_csv(csv_file):
    pol_ids = []
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0]:
                pol_ids.extend(search_and_add(row[0]))

    step("Trobades {} pòlisses", len(pol_ids))
    return pol_ids


def main(polissa_names, fitxer_csv, state, doit):
    if doit:
        success("Es FARAN CANVIS!")
    else:
        success("NO es faran canvis!")

    step("")
    step("cercant polisses.")
    if polissa_names:
        pol_ids = search_polisses_by_name(polissa_names)
    elif fitxer_csv:
        pol_ids = search_polisses_by_csv(fitxer_csv)
    else:
        pol_ids = []

    step("")
    step("trobades {} pòlisses a tractar.", len(pol_ids))
    modifieds = []
    errors = []
    for pol_id in tqdm(pol_ids):
        if modify_solar_flux(pol_id, state, doit):
            modifieds.append(pol_id)
        else:
            errors.append(pol_id)

    step("")
    step("Polisses modificades {} polisses.", len(modifieds))
    if modifieds:
        modifieds = pol_obj.read(modifieds, ['name'])
        step(",".join([modified['name'] for modified in modifieds]))

    step("")
    step("Polisses sense flux: {}", len(errors))
    if errors:
        errors = pol_obj.read(errors, ['name'])
        step(",".join([error['name'] for error in errors]))

    if doit:
        success("S'HAN FET CANVIS!")
    else:
        success("NO s'han fet canvis!")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Activador desactivador de bateries virtuals'
    )

    parser.add_argument(
        '--doit',
        dest='doit',
        help="Realitzar els canvis"
    )

    parser.add_argument(
        '--polissa_names',
        dest='pol_names',
        help="Nom de polisses"
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        help="csv amb el nom de les pòlisses (a la primera columna i sense capçalera)"
    )

    parser.add_argument(
        '--state',
        dest='state',
        help="Estat a assiganr"
    )

    args = parser.parse_args()
    try:
        main(
            args.pol_names,
            args.csv_file,
            args.state,
            args.doit == 'si'
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4
