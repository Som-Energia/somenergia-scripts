# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import csv
import traceback
from erppeek import Client
from tqdm import tqdm
from datetime import datetime
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
        f.write("id F1,Cups,fase importacio ,ID F1 rectificant, Fase importacio R\n")
        for a in content:
            f.write("{},{},{},{},{}\n".format(
                a['id'], a['cups'], a['fase'], a['id rect'], a['fase rect'])
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
                ff_d_f1 = set([f1.fecha_factura_desde])
                f_d = set(f1.importacio_lectures_ids.fecha_desde)
                if ff_d_f1 != f_d:
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

            if not rs:
                problematics_sense_R.append(problematic)
                dades = {'id':prob.id, 'cups': prob.cups_id.name, 'fase':prob.import_phase, 'id rect': False, 'fase rect': False}
                resultat.append(dades)
            for f1_r in rs:
                rect = f1_obj.browse(f1_r)
                dades = {'id':prob.id, 'cups': prob.cups_id.name, 'fase':prob.import_phase, 'id rect': rect.id, 'fase rect': rect.import_phase}
                dades['id_rect'] = rs[0]
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
