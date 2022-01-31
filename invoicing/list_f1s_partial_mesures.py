# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import csv
import traceback
from erppeek import Client
from tqdm import tqdm
from datetime import datetime, timedelta
import sys
from consolemsg import error, step, success, warn

import configdb
step("Connectant a l'erp")
c = Client(**configdb.erppeek)
step("Connectat")


errors_buscant = []

def output_results():
    success("Errors: ")
    step(errors_buscant)

def write_results(filename, content):
    with open(filename,'w') as f:
        f.write("id F1,Cups,fase importacio,tipus F1, Data factura desde, data factura hasta, data lect. anterior, data lect. actual,  ID F1 rectificant, Fase importacio R\n")
        for a in content:
            f.write("{},{},{},{},{}\n".format(
                a['id'], a['cups'], a['fase'],
                a['type'], a['fecha_desde'], a['fecha_hasta'],
                a['data_l_desde'], a['data_l_hasta'],
                a['id rect'], a['fase rect'])
            )

def find_f1s(from_date, to_date):

    search_params = [('data_carrega', '>=', from_date),
                     ('data_carrega', '<=', '{} 23:59:59'.format(to_date))]

    f1_obj = c.model('giscedata.facturacio.importacio.linia')
    f1s = f1_obj.search(search_params)

    problematics = []
    for f1 in tqdm(f1_obj.browse(f1s)):
        try:
            if f1.importacio_lectures_ids:
                ff_d_f1 = f1.fecha_factura_desde
                dia_anterior = (datetime.strptime(f1.fecha_factura_desde, '%Y-%m-%d') - timedelta(days=1)).strftime("%Y-%m-%d")
                f_d = min(f1.importacio_lectures_ids.fecha_desde)
                f_h_lect = max(f1.importacio_lectures_ids.fecha_actual)
                if (f_d not in [dia_anterior, ff_d_f1]) or f_h_lect != f1.fecha_factura_hasta:
                    problematics.append(f1.id)
        except Exception as e:
            errors_buscant.append(str(e))
            step("Error: {}", str(e))
            traceback.print_exc(file=sys.stdout)

    problematics_sense_R = []
    f1_sense_cups = []
    resultat = []
    for problematic in tqdm(problematics):
        try:
            rs = []
            prob = f1_obj.browse(problematic)
            if not prob.cups_id:
                f1_sense_cups.append(problematic)
                continue
            rs = f1_obj.search([('cups_id','=',prob.cups_id.id),
                                ('codi_rectificada_anulada','!=',False),
                                ('codi_rectificada_anulada','=',prob.invoice_number_text),
                                ('type_factura','=','R')])

            dades_f1 = {
                'id': prob.id, 'cups': prob.cups_id.name, 'fase': prob.import_phase,
                'type': prob.type_factura, 'id rect': False, 'fase rect': False,
                'fecha_desde': prob.fecha_factura_desde, 'fecha_hasta': prob.fecha_factura_hasta,
                'data_l_desde': min(prob.importacio_lectures_ids.fecha_desde),
                'data_l_hasta': max(prob.importacio_lectures_ids.fecha_actual)
            }
            if not rs:
                problematics_sense_R.append(problematic)
                resultat.append(dades_f1)
            for f1_r in rs:
                rect = f1_obj.browse(f1_r)
                dades = dades_f1.copy()
                dades['id_rect'] = rect.id
                dades['fase rect'] = rect.import_phase
                resultat.append(dades)
        except Exception as e:
            errors_buscant.append(str(e))
            step("Error: {}", str(e))
            traceback.print_exc(file=sys.stdout)

    return resultat


def main(from_date, to_date, filename='output.csv'):

    content = find_f1s(from_date, to_date)
    output_results()
    write_results(filename, content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatische Kunde Profile erstellen'
    )

    parser.add_argument(
        '--from-date',
        dest='from_date',
        required=True,
        help="Data de càrrega a partir de la qual cal buscar els F1"
    )

    parser.add_argument(
        '--to-date',
        dest='to_date',
        required=True,
        help="Data de càrrega fins la que cal buscar els F1"
    )

    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        help="Output csv file",
        )
    args = parser.parse_args()

    try:
        main(args.from_date, args.to_date, args.output)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Chao!")
