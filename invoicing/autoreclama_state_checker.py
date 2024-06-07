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

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
pol_obj = O.GiscedataPolissa
imd_obj = O.IrModelData
polhh_obj = O.SomAutoreclamaStateHistoryPolissa
subtr_obj = O.GiscedataSubtipusReclamacio
atc_obj = O.GiscedataAtc


review_state_id = imd_obj.get_object_reference(
    "som_autoreclama", "review_state_workflow_polissa"
)[1]


def days_between(a, b):
    a = datetime.strptime(a, "%Y-%m-%d")
    b = datetime.strptime(b, "%Y-%m-%d")
    return (b - a).days


def today_minus_days(days):
    days_ago = datetime.today() - timedelta(days=days)
    return datetime.strftime(days_ago, "%Y-%m-%d")


def search_and_add(pol_name):
    pol_name = pol_name.strip().zfill(7)
    step("Cerquem la polissa... {}", pol_name)
    found_ids = pol_obj.search(
        [('name', '=', pol_name)],
        context={'active_test': False}
    )

    if len(found_ids) != 1:
        warn(
            "item {} ha trobat {} polisses! {}",
            pol_name, len(found_ids), found_ids
        )
        return []

    found_id = found_ids[0]
    step("Trobada id {} afegint", found_id)
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


def add_day(base, key, date, today_str):
    if date:
        base['data_' + key] = date
        base['dies_' + key] = days_between(date[:10], today_str)
    else:
        base['data_' + key] = ''
        base['dies_' + key] = 'F'


def main(polissa_names, fitxer_csv, date_offset):
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
    today_str = today_minus_days(date_offset if date_offset else 0)
    step("dia agafat com avui >{}<", today_str)

    result = {}
    for pol_id in tqdm(pol_ids):
        pol = pol_obj.browse(pol_id)

        polissa = {}
        polissa['numero'] = pol.name
        polissa['estat'] = pol.state
        polissa['activa'] = pol.active

        add_day(polissa, 'baixa', pol.data_baixa, today_str)
        add_day(polissa, 'ultima_lectura_f1', pol.data_ultima_lectura_f1, today_str)

        polissa['facturat'] = (
            polissa['data_baixa'] and
            polissa['data_ultima_lectura_f1'] == polissa['data_baixa'] and
            polissa['estat'] == 'baixa')

        if polissa['data_baixa']:
            polissa['facturat'] = (
                polissa['data_ultima_lectura_f1'] == polissa['data_baixa'] and
                polissa['estat'] == 'baixa'
            )
            polissa['antiga'] = days_between(polissa['data_baixa'], today_str) > 300
        else:
            polissa['facturat'] = '-'
            polissa['antiga'] = False

        states = len(pol.autoreclama_history_ids)
        if states > 0:
            polissa['estat_autoreclama_actual'] = pol.autoreclama_history_ids[0].state_id.name
        else:
            polissa['estat_autoreclama_actual'] = 'No'

        if states > 1:
            polissa['estat_autoreclama_anterior'] = pol.autoreclama_history_ids[1].state_id.name
        else:
            polissa['estat_autoreclama_anterior'] = 'No'

        first = True
        found_cases = 0
        last_case_close_date = ''
        last_case_state = ''
        for c, h in enumerate(pol.autoreclama_history_ids):
            if h.generated_atc_id:
                found_cases += 1
                if first:
                    last_case_close_date = h.generated_atc_id.date_closed
                    last_case_state = h.generated_atc_id.state
                    first = False
            if h.state_id.id == review_state_id and c != 0:
                break

        polissa['cassos_atc_006_previs'] = found_cases
        polissa['estat_ultim_atc_006'] = last_case_state
        add_day(polissa, 'tancament_ultim_atc_006', last_case_close_date, today_str)
        result[pol_id] = polissa

    step("")
    success("Resum")
    step("Polissa      Estat Ac   D.Baixa dies  Ultim f1 dies  FACT ANTG       Estat actual         Estat previ  006 Estat      Ultim tancament dies")
    for pol_id in sorted(result.keys()):
        v = result[pol_id]
        step(
            "{} {:>10}  {:1} {:>10} {:>3} {:>10} {:>3}    {:1}    {:1}   >{:>16}<  >{:>16}< {:>3} {:>6} {:>7} {}",
            v['numero'],
            v['estat'],
            v['activa'],
            v['data_baixa'],
            v['dies_baixa'],
            v['data_ultima_lectura_f1'],
            v['dies_ultima_lectura_f1'],
            v['facturat'],
            v['antiga'],
            v['estat_autoreclama_actual'][:16],
            v['estat_autoreclama_anterior'][:16],
            v['cassos_atc_006_previs'],
            v['estat_ultim_atc_006'],
            v['data_tancament_ultim_atc_006'],
            v['dies_tancament_ultim_atc_006'],
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='verificador de dades de polisses autoreclama'
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
        '--days',
        type=int,
        dest='days',
        help="dies a restar al avui"
    )

    args = parser.parse_args()
    try:
        main(
            args.pol_names,
            args.csv_file,
            args.days,
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4
