#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import traceback
from erppeek import Client
import configdb
import argparse
import sys
from consolemsg import error, step, success, warn
from tqdm import tqdm
from datetime import datetime, timedelta

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
pol_obj = O.GiscedataPolissa
imd_obj = O.IrModelData
polhh_obj = O.SomAutoreclamaStateHistoryPolissa
subtr_obj = O.GiscedataSubtipusReclamacio
atc_obj = O.GiscedataAtc


# ddbb constants
correct_state_id = imd_obj.get_object_reference(
    "som_autoreclama", "correct_state_workflow_polissa"
)[1]
loop_state_id = imd_obj.get_object_reference(
    "som_autoreclama", "loop_state_workflow_polissa"
)[1]
disabled_state_id = imd_obj.get_object_reference(
    "som_autoreclama", "disabled_state_workflow_polissa"
)[1]

state_names = {
    correct_state_id: u"Correcte",
    loop_state_id: u"Reclamació Bucle",
    disabled_state_id: u"Desactivat - Gestió Manual",
}


def today_minus_days(days):
    days_ago = datetime.today() - timedelta(days=days)
    return datetime.strftime(days_ago, "%Y-%m-%d %H:%M:%S")


def historize(doit, pol_id, state_id, a, b):
    if doit:
        polhh_obj.historize(pol_id, state_id, a, b)


def search_actual_r1_006_for_polissa(pol_id):
    subtr_id = subtr_obj.search([("name", "=", "006")])[0]
    search_params = [
        ("state", "in", ['open', 'pending']),
        ("polissa_id", "=", pol_id),
        ("subtipus_id", "=", subtr_id),
    ]

    atc_ids = atc_obj.search(search_params, order='id desc')
    if atc_ids:
        return atc_ids[0]

    search_params = [
        ("state", "in", ['open', 'pending', 'done']),
        ("polissa_id", "=", pol_id),
        ("subtipus_id", "=", subtr_id),
        ("date", ">", today_minus_days(300))
    ]

    atc_ids = atc_obj.search(search_params, order='id desc')
    if atc_ids:
        return atc_ids[0]

    return False


def search_polisses_to_activate():
    pol_actives_ids = pol_obj.search(
        [
            ("state", "in", ['activa', 'impagament', 'modcontractual']),
            ("autoreclama_state", "=", None),
        ],
        context={'active_test': False},
    )
    step(
        "trobades {} polisses actives,impagades o en mod sense autoreclama",
        len(pol_actives_ids)
    )

    pol_baixa_ids = pol_obj.search(
        [
            ("state", "=", 'baixa'),
            ("data_baixa", ">", today_minus_days(300)[:10]),
            ("autoreclama_state", "=", None),
        ],
        context={'active_test': False},
    )
    step(
        "trobades {} polisses de baixa de fa meny de 300 dies",
        len(pol_baixa_ids)
    )

    pol_ids = sorted(list(set(pol_actives_ids + pol_baixa_ids)))
    step("trobades {} polisses en total", len(pol_ids))
    return pol_ids


def search_polisses_by_name(pol_names, overwrite):
    pol_ids = []

    pol_names_list = pol_names.split(',')
    step("Trobades {} noms de possibles pòlisses", len(pol_names_list))
    for pol_name in tqdm(pol_names_list):
        if len(pol_name) != 7:
            pol_name = pol_name.zfill(7)

        found_ids = pol_obj.search(
            [('name', '=', pol_name)],
            context={'active_test': False}
        )

        if len(found_ids) != 1:
            warn("item {} ha trobat {} polisses!", pol_name, len(found_ids))
        else:
            found_id = found_ids[0]
            if overwrite:
                pol_ids.append(found_id)
            else:
                pol_data = pol_obj.read(found_id, ['autoreclama_state'])
                if pol_data['autoreclama_state']:
                    warn("item {} ja te estat autoreclama eskipant.", pol_name)
                else:
                    pol_ids.append(found_id)

    step("Trobades {} pòlisses", len(pol_ids))
    return pol_ids


def main(polissa_names, state, batch_size, overwrite_state, doit):
    if doit:
        success("Es FARAN CANVIS!")
    else:
        success("NO es faran canvis!")

    step("")
    step("cercant polisses.")
    if polissa_names:
        pol_ids = search_polisses_by_name(polissa_names, overwrite_state)
    else:
        pol_ids = search_polisses_to_activate()

    step("")
    step("trobades {} pòlisses a tractar.", len(pol_ids))
    if batch_size:
        pol_ids = pol_ids[:batch_size]
        step("limitant a les primeres {} pòlisses.", batch_size)

    result = {}
    for pol_id in tqdm(pol_ids):
        atc_006_id = None
        if state in ['loop', 'auto']:
            atc_006_id = search_actual_r1_006_for_polissa(pol_id)
            if state == 'loop':
                state_id = loop_state_id
            if state == 'auto':
                state_id = loop_state_id if atc_006_id else correct_state_id
        if state == 'disabled':
            state_id = disabled_state_id
        if state == 'correct':
            state_id = correct_state_id

        if state_id not in result:
            result[state_id] = [pol_id]
        else:
            result[state_id].append(pol_id)
        historize(doit, pol_id, state_id, None, atc_006_id)

    step("")
    step("Resum")
    for stat in sorted(result.keys()):
        success(
            "Estat autoreclama >{}< assignat a {} polisses",
            state_names[stat],
            len(result[stat])
        )

    step("")
    step("Polisses:")
    for stat in sorted(result.keys()):
        success("Estat autoreclama >{}< polisses:", state_names[stat])
        step(
            "{}",
            ', '.join(
                [p['name'] for p in pol_obj.read(result[stat], ['name'])]
            )
        )

    if doit:
        success("S'HAN FET CANVIS!")
    else:
        success("NO s'han fet canvis!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Cercador de contractes a activar autoreclama'
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
        '--initial_state',
        dest='initial_state',
        help="Estat inicial a assignar"
    )

    parser.add_argument(
        '--overwrite_state',
        dest='overwrite_state',
        help="Sobrescriu el esta d'autoreclama"
    )

    parser.add_argument(
        '--batch',
        type=int,
        dest='batch',
        help="Mida màxima del grupo de polisses a activar"
    )

    args = parser.parse_args()
    try:
        main(
            args.pol_names,
            args.initial_state,
            args.batch,
            args.overwrite_state == 'True',
            args.doit == 'si'
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4
