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
pol_o = c.GiscedataPolissa
f1_obj = c.GiscedataFacturacioImportacioLinia

pols_to_check_ids = []
errors_buscant = []


def find_empty_periods(from_date):
    forats = []
    for p_id in tqdm(pols_to_check_ids):
        try:
            p = pol_o.browse(p_id)
            cups_id = p.cups.id
            data_a_partir = from_date if p.data_alta < from_date else p.data_alta
            f1ns = f1_obj.search([('cups_id','=',cups_id), ('tipo_factura_f1','=','atr'), ('fecha_factura_desde','>',data_a_partir)], order='fecha_factura_desde asc')
            fins_previ = ''; desde_previ = ''
            if f1ns:
                type_fact_f1ns = f1_obj.read(f1ns, ['type_factura'])
            for a in f1ns:
                f1 = f1_obj.browse(a)
                hasta = f1.fecha_factura_hasta
                desde = f1.fecha_factura_desde
                if not fins_previ:
                    fins_previ = hasta
                    desde_previ = desde
                else:
                    if fins_previ == hasta and desde == desde_previ:
                        continue
                    if desde != fins_previ:
                        forats.append({
                            'f1_id':f1.id, 'cups':f1.cups_id.name, 'desde': fins_previ, 'hasta':desde,
                            'p_id': p_id, 'polissa': p.name, 'distri': p.distribuidora.name, 'mode_fac': p.facturacio_potencia,
                            'autoconsum': p.autoconsumo, 'data_alta_auto': p.data_alta_autoconsum, 'tarifa': p.tarifa.name,
                            'tipus_f1_cups': ', '.join([t['type_factura'] for t in type_fact_f1ns])
                        })
                    fins_previ = hasta
                    desde_previ = desde
        except (KeyboardInterrupt, SystemExit, SystemError):
            warn("Aarrggghh you kill me :(")
            raise KeyboardInterrupt()
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            error_text = ''
            try:
                error_text = str(e)
            except UnicodeEncodeError as e2:
                error_text = unicode(e)
            except:
                error_text = "Text d'error desconegut"
            errors_buscant.append(error_text)

    return forats

def output_results(result):
    success("Resultat final")
    success("----------------")
    success("Pòlisses analitzades: {}",len(pols_to_check_ids))

    success("Forats trobats: {}",len(result))

    success("Errors: ")
    step(','.join(errors_buscant))


def write_results(filename, result):
    fieldnames = ['f1_id','p_id', 'polissa','cups','distri','desde','hasta','tarifa','mode_fac','autoconsum','data_alta_auto','tipus_f1_cups']

    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in result:
            writer.writerow({k: unicode(v).encode('utf-8') for k, v in a.items()})

def read_polissa_names(csv_file):
    one_id = pol_o.search([], limit=1)[0]
    one_name = pol_o.read(one_id, ['name'])['name']
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        csv_content = [row[0].zfill(len(one_name)) for row in reader if row and row[0]]
    return list(set(csv_content))


def search_polissa_by_names(polissa_names):
    ret_ids = []
    for polissa_name in polissa_names:
        step("Cerquem la polissa...", polissa_name)
        pol_ids = pol_o.search([('name', '=', polissa_name)], context={'active_test': False})
        if len(pol_ids) == 0:
            warn("Cap polissa trobada amb aquest id!!")
        elif len(pol_ids) > 1:
            warn("Multiples polisses trobades!! {}", pol_ids)
        else:
            ret_ids.append(pol_ids[0])
            step("Polissa amb ID {} existeix", pol_ids[0])
    return ret_ids

def main(input_file, from_date, filename='output.csv'):
    if input_file:
        pols_to_check_ids.extend(search_polissa_by_names(read_polissa_names(input_file)))
    else:
        step("Busquem totes les pòlisses que han estat actives des de la data indicada fins avui, encara que ja estiguin de baixa")
        pols_to_check_ids.extend(pol_o.search([('data_ultima_lectura_f1','>', from_date),'|',('data_baixa','=', False),('data_baixa', '>=', from_date)], context={'active_test': False}))
    result = find_empty_periods(from_date)
    output_results(result)
    write_results(filename, result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatische Kunde Profile erstellen'
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        required=False,
        help="csv amb el nom de les pòlisses a comprovar"
    )
    parser.add_argument(
        '--from-date',
        dest='from_date',
        required=True,
        help="Data a partir de la qual buscar períodes sense F1"
    )
    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        help="Output csv file",
        )
    args = parser.parse_args()

    try:
        main(args.csv_file, args.from_date, args.output)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Chao!")
