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
fact_obj = c.model('giscedata.facturacio.factura')

no_correspon_prov = []
no_correspon_prov_ids = []
differents = []
facts_ok = []

errors_buscant = []

def output_results():
    success("Resultat final")
    success("----------------")
    success("Factures ok: {}",len(facts_ok))

    success("----------------")
    success("Factures pels quals no s'ha trobat una (i només una) factura de proveidor: {}",len(no_correspon_prov_ids))
    success(no_correspon_prov_ids)
    if len(no_correspon_prov_ids) != 0:
        success("--- Id factura client i número de fact.proveidor trobades:")
        [success("--- {},{}".format(a[0], a[1])) for a in no_correspon_prov]

    success("Factures on difereix l'energia exportada respecte a la factura de proveidor: {}",len(differents))

    success("Errors: ")
    step(errors_buscant)


def write_results(filename):
    with open(filename,'w') as f:
        f.write("Polissa,ID factura,Num Factura,Exportada client, Exportada proveidor, data inici, data final,ID factura proveidor, observacions\n")
        for a in differents:
            f.write("{},{},{},{},{},{},{},{},{}\n".format(
                a['polissa'], a['f_id'], a['f_num'], a['exp_client'], a['exp_prov'], a['data_inici'], a['data_final'], a['f_prov_id'], a['obs'])
            )


def find_invoices(from_date, to_date):
    pols_ids = pol_o.search([('autoconsumo','!=','00'),('data_alta','<=',to_date),'|',('data_baixa','=',False),('data_baixa','>=',from_date)], context={'active_test':False})
    pols_info = pol_o.read(pols_ids, ['data_alta_autoconsum'])
    for p_info in tqdm(pols_info):
        try:
            date_from = from_date if from_date > p_info['data_alta_autoconsum'] else p_info['data_alta_autoconsum']
            p_id = p_info['id']
            f_ids = fact_obj.search([('polissa_id','=',p_id),('data_final','>=', date_from), ('data_inici', '<=', to_date)])
            if not f_ids:
                continue
            f_client_ids = fact_obj.search([('id','in',f_ids),('type','=','out_invoice'),('refund_by_id','=',False)])
            for f_c_id in f_client_ids:
                fact = fact_obj.browse(f_c_id)
                f_prov_id = fact_obj.search([('id','in',f_ids),('type','=','in_invoice'),('data_inici','=',fact.data_inici),('data_final','=',fact.data_final),('refund_by_id','=',False)])
                if len(f_prov_id) > 1:
                    no_correspon_prov_ids.append(f_c_id)
                    no_correspon_prov.append([f_c_id, len(f_prov_id)])
                elif len(f_prov_id) == 0:
                    f_prov_extrems_ids = fact_obj.search([('polissa_id', '=', p_id), ('type', '=', 'in_invoice'), '|',('data_final', '=', fact.data_final), ('data_inici','=', fact.data_inici)])
                    if len(f_prov_extrems_ids) == 1:
                        fact_prov = fact_obj.browse(f_prov_extrems_ids[0])
                        f_clients_partides_id = fact_obj.search([('polissa_id','=',p_id),('type','=','out_invoice'),('data_inici','>=', fact_prov.data_inici), ('data_final','<=', fact_prov.data_final)])
                        if f_clients_partides_id:
                            energy_total = sum([x['generacio_kwh'] for x in fact_obj.read(f_clients_partides_id, ['generacio_kwh'])])
                            if abs(fact_prov.generacio_kwh - energy_total) > len(f_clients_partides_id):
                                differents.append({
                                    'f_id':fact.id, 'f_num': fact.number, 'polissa':fact.polissa_id.name,
                                    'exp_client':fact.generacio_kwh, 'exp_prov':fact_prov.generacio_kwh,
                                    'f_prov_id':fact_prov.id, 'data_inici':fact.data_inici, 'data_final':fact.data_final, 'obs': 'Comprèn una part de la factura de proveïdor'
                                })
                    else:
                        no_correspon_prov.append([f_c_id, len(f_prov_id)])
                else:
                    fact_prov = fact_obj.browse(f_prov_id[0])
                    if abs(fact_prov.generacio_kwh - fact.generacio_kwh) > 2:
                        differents.append({
                            'f_id':fact.id, 'f_num': fact.number, 'polissa':fact.polissa_id.name,
                            'exp_client':fact.generacio_kwh, 'exp_prov':fact_prov.generacio_kwh,
                            'f_prov_id':fact_prov.id, 'data_inici':fact.data_inici, 'data_final':fact.data_final, 'obs':''
                        })
                    else:
                        facts_ok.append(f_c_id)

        except Exception as e:
            errors_buscant.append(str(e))
            step("Error: {}", str(e))
            traceback.print_exc(file=sys.stdout)


def main(from_date, to_date, filename='output.csv'):

    find_invoices(from_date, to_date)
    output_results()
    write_results(filename)


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
