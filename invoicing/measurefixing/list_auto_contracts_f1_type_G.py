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
f1_obj = c.model('giscedata.facturacio.importacio.linia')

no_trobats = []; no_auto = []; no_negatiu = []; altres_auto = []


multiple_atrinvoices = [] # f1 with multiple atr invoices
errors_buscant = []
ja_facturats = []
no_facturats = []

def output_results():
    success("Resultat final")
    success("----------------")
    success("Amb autoconsum != 41: {}",len(altres_auto))
    success("CUPS amb F1 tipus G amb cap linia d'energia negativa: {}",len(no_negatiu))
    success("CUPS amb F1 tipus G sense línies de generació: {}",len(no_auto))
    success("Pòlisses amb F1 tipus G ja facturat: {}",len(ja_facturats))
    success("Pòlisses amb F1 tipus G no facturats: {}",len(ja_facturats))
    success("----------------")
    success("----------------")
    success("F1'ns pels quals no s'ha trobat la pòlissa: {}",len(no_trobats))
    success(no_trobats)

    if len(multiple_atrinvoices) != 0:
        success("F1ns que informen de més d'una FacturaATR: {}",len(multiple_atrinvoices))
        step(multiple_atrinvoices)
    success("Errors: ")
    step(','.join(errors_buscant))


def write_results(filename, show_fact):
    to_write = no_facturats[:]
    if show_fact:
        to_write += ja_facturats
    with open(filename,'w') as f:
        f.write("polissa,data ultima lectura,data ultima lect f1, data des de f1G,data fins f1G,te gkwh, autoconsum\n")
        for a in to_write:
            f.write("{},{},{},{},{},{},{}\n".format(a['name'],a['data_ultima_lectura'],a['data_ultima_lectura_f1'],a['fecha_desde'],a['fecha_hasta'],a['te_assignacio_gkwh'], a['autoconsumo']))


def find_f1_g(from_date):
    pols = []
    dades_pols = []
    try:
        f1_g = f1_obj.search([('fecha_factura_desde','>', from_date),('type_factura','=','G')])

        for f1_id in tqdm(f1_g):
            f1 = f1_obj.browse(f1_id)
            l_ener = []; l_gen = []
            if len(f1.liniafactura_id) > 1:
                multiple_atrinvoices(f1.id)
            for lf in f1.liniafactura_id:
                if lf.linies_generacio:
                    l_ener += lf.linies_energia.quantity
            if not l_ener:
                no_auto.append(f1_id)
                continue
            if min(l_ener) >= 0:
                no_negatiu.append(f1_id)
                continue
            p_id = pol_o.search([('cups','=', f1.cups_id.id),('data_alta','<=',f1.fecha_factura_desde),'|',('data_baixa','=',False),('data_baixa','>=',f1.fecha_factura_hasta)], context={'active_test':False})
            if p_id:
                p_id = p_id[0]
                pols.append(p_id)
                info = pol_o.read(p_id, ['name','data_ultima_lectura','data_ultima_lectura_f1','te_assignacio_gkwh', 'autoconsumo'], context={'date':f1.fecha_factura_desde})
                info.update({'f1_id': f1_id, 'fecha_desde':f1.fecha_factura_desde, 'fecha_hasta':f1.fecha_factura_hasta})
                if info['autoconsumo'] != '41':
                    altres_auto.append(info)
                else:
                    dades_pols.append(info)
            else:
                no_trobats.append(f1_id)

        no_facturats.extend(list(filter(lambda x: x['data_ultima_lectura'] < x['fecha_hasta'],dades_pols)))
        ja_facturats.extend(list(filter(lambda x: x['data_ultima_lectura'] >= x['fecha_hasta'],dades_pols)))
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


def main(from_date, show_fact, filename='output.csv'):

    find_f1_g(from_date)
    output_results()
    write_results(filename, show_fact)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatische Kunde Profile erstellen'
    )

    parser.add_argument(
        '--show-fact',
        dest='show_fact',
        required=True,
        help="Mostrar els F1 tipus G ja facturats?"
    )

    parser.add_argument(
        '--from-date',
        dest='from_date',
        required=True,
        help="Data a d'inici del consum a partir de la qual es busquen els F1 tipus G"
    )
    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        help="Output csv file",
        )
    args = parser.parse_args()

    try:
        show_fact = args.show_fact == 's'
        main(args.from_date, show_fact, args.output)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Chao!")
