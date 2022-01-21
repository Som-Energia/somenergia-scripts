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


no_correspon_prov = []
differents = []
facts_ok = []
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
    step(errors_buscant)


def write_results(filename, show_fact):
    to_write = no_facturats[:]
    if show_fact:
        to_write += ja_facturats
    with open(filename,'w') as f:
        f.write("polissa,data ultima lectura,data ultima lect f1, data des de f1G,data fins f1G,te gkwh, autoconsum\n")
        for a in to_write:
            f.write("{},{},{},{},{},{},{}\n".format(a['name'],a['data_ultima_lectura'],a['data_ultima_lectura_f1'],a['fecha_desde'],a['fecha_hasta'],a['te_assignacio_gkwh'], a['autoconsumo']))


def find_invoices(from_date, to_date):
    pols_ids = pol_o.search([('autoconsumo','!=','00')('data_alta','<=',to_date),'|',('data_baixa','=',False),('data_baixa','>=',from_date)], context={'active_test':False})
    pols_info = pol_o.read(pols_ids, ['data_alta_autoconsum'])
    dades_pols = []
    try:
        for p_info in tqdm(pols_info):
            date_from = from_date if from_date > p_info['data_alta_autoconsum'] else p_info['data_alta_autoconsum']
            p_id = p_info['id']
            f_ids = fact_obj.search([('polissa_id','=',p_id),('data_inici','>=', date_from), ('data_inici', '<', to_date)])
            if not f_ids:
                continue
            f_client_ids = fact_obj.search([('id','in',f_ids),('type','=','out_invoice'),('refund_by_id','=',False)])
            for f_c_id in tqdm(f_client_ids):
                fact = fact_obj.browse(f_c_id)
                f_prov_id = fact_obj.search([('id','in',f_ids),('type','=','in_invoice'),('data_inici','=',fact.data_inici),('data_final','=',fact.data_final)])
                if len(f_prov_id) != 1:
                    no_correspon_prov.append([f_c_id, len(f_prov)])
                else:
                    fact_prov = fact_obj.browse(f_prov[0])
                    if abs(fact_prov.generacio_kwh - fact.generacio_kwh) > 2:
                        differents.append({
                            'f_id':fact.id, 'polissa':fact.polissa_id.name,
                            'exp_client':fact.generacio_kwh, 'exp_prov':fact_prov.generacio_kwh,
                            'f_prov_id':fact_prov.id, 'data_inici':fact.data_inici, 'data_final':fact.data_final
                        })
                    else:
                        facts_ok.append(f_c_id)

    except Exception as e:
        errors_buscant.append(str(e))
        step("Error: {}", str(e))
        traceback.print_exc(file=sys.stdout)


def main(from_date, show_fact, filename='output.csv'):

    find_f1_g(from_date)
    output_results()
    write_results(filename, show_fact)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatische Kunde Profile erstellen'
    )

    parser.add_argument(
        '--from-date',
        dest='from_date',
        required=True,
        help="Data a d'inici del consum a partir de la qual es busquen les factures"
    )

    parser.add_argument(
        '--to-date',
        dest='to_date',
        required=True,
        help="Data fi del consum a partir de la qual es busquen les factures"
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
