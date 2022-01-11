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
lect_obj = c.GiscedataLecturesLectura

missing_names = []  #noms de pòlisses no trobades
altres_auto = [] #polisses amb autoconsum != 41
sense_f1_g = []  #polisses per les quals no s'ha trobat un f1G no facturat
f1_more_atrfact = [] #Cups de F1 amb més d'una factura dins de l'f1
ja_facturats = [] #L'F1 ja està facturat
no_auto = [] #l'F1 no té línies de generació
no_negatiu = [] # l'F1 no té cap línia d'energia quantitat negativa
sense_lect_pre = []; sense_lect_post = []; no_3_lect_pre = []; no_3_lect_post = []; err_lect_post = []
set_zero_c = [] #polisses processades ok
errors_processant = []
errors_buscant = []


def output_results(filename):
    success("Resultat final")
    success("--------------")

    success("Número de Polisses processades: {}", len(set_zero_c))

    success("ERRORS inicials:")
    success("----------------")
    success("Pòlisses no trobades: {}",len(missing_names))
    step(missing_names)
    success("Amb autoconsum != 41: {}",len(altres_auto))
    step(altres_auto)
    success("CUPS amb F1 tipus G amb cap linia d'energia negativa: {}",len(no_negatiu))
    step(no_negatiu)
    success("CUPS amb F1 tipus G sense línies de generació: {}",len(no_auto))
    step(no_auto)
    success("Pòlisses amb F1 tipus G ja facturat: {}",len(ja_facturats))
    step(ja_facturats)
    success("Sense F1 tipus G no facturat: {}",len(sense_f1_g))
    step(sense_f1_g)
    if f1_more_atrfact:
        success("Més d'una factura dins de l'F1 [CUPS](cal revisar acció feta): {}",len(f1_more_atrfact))
        step(f1_more_atrfact)
    success("Altres errors: {}", len(errors_buscant))
    print_list(errors_buscant)


    success("Processant les pòlisses:")
    success("-------------------------------")
    success("Sense lectures carregades de data inicial de l'F1: {}",len(sense_lect_pre))
    step(sense_lect_pre)
    success("Nombre de lectures inicials diferents de 3: {}",len(no_3_lect_pre))
    step(no_3_lect_pre)
    success("Nombre de lectures finals diferents de 3: {}",len(no_3_lect_post))
    step(no_3_lect_post)
    success("Error en trobar alguna lectura final: {}",len(err_lect_post))
    step(err_lect_post)
    success("Altres errors: {}", len(errors_processant))
    print_list(errors_processant)

    with open(filename,'w') as f:
        f.write('\n'.join(set_zero_c))

def print_list(lst):
    for item in lst:
        pol_name = item[0]
        pol_text = item[1]
        step("polissa {}", pol_name)
        step(pol_text)


def read_polissa_names(csv_file):
    one_id = pol_o.search([], limit=1)[0]
    one_name = pol_o.read(one_id, ['name'])['name']
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        csv_content = [row[0].zfill(len(one_name)) for row in reader if row[0]]
    return list(set(csv_content))

def find_pol_data(pol_names, from_date):
    pol_ids = pol_o.search([('name', 'in', pol_names)], context={'active_test': False})
    if not pol_ids:
        return []

    pol_data = pol_o.read(pol_ids, ['name','cups'])
    pols_cups = [x['cups'][0] for x in pol_data]

    if len(pol_data) != len(pol_names):
        found_names = [x['name'] for x in pol_data]
        missing_names = [n for n in pol_names if n not in found_names]
    pols = []; dades_pols = []; found_cups = []
    f1_g = f1_obj.search([('fecha_factura_desde','>=',from_date),('type_factura','=','G'), ('cups_id','in',pols_cups)])
    for f1_id in tqdm(f1_g):
        try:
            f1 = f1_obj.browse(f1_id)
            found_cups.append(f1.cups_id.id)
            l_ener = []; l_gen = []
            if len(f1.liniafactura_id) > 1:
                f1_more_atrfact.append(f1.cups_id.name)
            for lf in f1.liniafactura_id:
                if lf.linies_generacio:
                    l_ener += lf.linies_energia.quantity
            if not l_ener:
                no_auto.append(f1.cups_id.name)
                continue
            if min(l_ener) >= 0:
                no_negatiu.append(f1.cups_id.name)
                continue
            p_id = pol_o.search([('cups','=', f1.cups_id.id),('data_alta','<=',f1.fecha_factura_desde),'|',('data_baixa','=',False),('data_baixa','>=',f1.fecha_factura_hasta)], context={'active_test':False})
            if p_id and p_id[0] in pol_ids:
                p_id = p_id[0]
                info = pol_o.read(p_id, ['name','data_ultima_lectura','data_ultima_lectura_f1','te_assignacio_gkwh', 'autoconsumo'], context={'date':f1.fecha_factura_desde})
                info.update({'f1_id': f1_id, 'fecha_desde':f1.fecha_factura_desde, 'fecha_hasta':f1.fecha_factura_hasta, 'quant_energia':l_ener})
                pols.append(info['name'])
                if info['autoconsumo'] != '41':
                    altres_auto.append(info)
                else:
                    dades_pols.append(info)
        except Exception as e:
            errors_buscant.append([p_dades['name'], str(e)])
            step("Error: {}", str(e))
            traceback.print_exc(file=sys.stdout)

    ja_facturats = [x['name'] for x in list(filter(lambda x: x['data_ultima_lectura'] >= x['fecha_hasta'],dades_pols))]
    no_facturats = list(filter(lambda x: x['data_ultima_lectura'] < x['fecha_hasta'],dades_pols))

    if len(found_cups) != len(pols_cups):
        cups_sense_f1_g = [x for x in pols_cups if x not in found_cups]
        pol_ids_sense_f1_g = pol_o.search([('id','in', pol_ids),('cups','in', cups_sense_f1_g)],context={'active_test': False})
        sense_f1_g.extend([x['name'] for x in pol_o.read(pol_ids_sense_f1_g, ['name'])])
    return no_facturats


def set_zero_consumption_GF1(pols_data):

    for p_dades in tqdm(pols_data):
        try:
            search_params = [('name','=', p_dades['fecha_desde']),('comptador.polissa','=',p_dades['id'])]

            lect_pre = lect_obj.search(search_params, context={'active_test': False})
            if len(lect_pre) == 0:
                sense_lect_pre.append(p_dades['name'])
                continue
            if len(lect_pre) != 3:
                no_3_lect_pre.append(p_dades['name'])
                continue
            lect_post = lect_obj.search([('name','=',p_dades['fecha_hasta']),('comptador.polissa','=',p_dades['id'])], context={'active_test': False})
            if len(lect_post) != 3:
                no_3_lect_post.append(p_dades['name'])
                continue
            done_ok = True
            for l in lect_obj.browse(lect_pre):
                l_post_id = lect_obj.search([('id','in',lect_post),('periode','=',l.periode.id)], context={'active_test': False})
                if len(l_post_id) != 1:
                    err_lect_post.append([p_dades, l.periode.id, l_post_id])
                    done_ok = False
                    break
                l_post = lect_obj.browse(l_post_id[0])
                lect_obj.write(l_post.id, {'ajust': l.lectura - l_post.lectura, 'ajust_exporta':l.lectura_exporta - l_post.lectura_exporta, 'observacions': 'Ajust per factura G.\n'+l_post.observacions})
            if done_ok:
                set_zero_c.append(p_dades['name'])
        except Exception as e:
            errors_processant.append([p_dades['name'], str(e)])
            step("Error: {}", str(e))
            traceback.print_exc(file=sys.stdout)

def main(csv_file, from_date, filename='output.csv'):

    csv_content = read_polissa_names(csv_file)
    pol_data = find_pol_data(csv_content, from_date)
    set_zero_consumption_GF1(pol_data)
    output_results(filename)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatische Kunde Profile erstellen'
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        required=True,
        help="csv amb el nom de les pòlisses a modificar (a la primera columna i sense capçalera)"
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
        main(args.csv_file, args.from_date, args.output)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Chao!")
