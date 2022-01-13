#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import configdb
import argparse, csv
import traceback
from erppeek import Client
from tqdm import tqdm
from datetime import datetime, timedelta
from consolemsg import step, success, error, warn
import sys


step("Connectant a l'erp")
c = Client(**configdb.erppeek)
step("Connectat")

pol_o = c.GiscedataPolissa
fact_obj = c.GiscedataFacturacioFactura
lect_obj = c.model('giscedata.lectures.lectura')
lect_pot_obj = c.model('giscedata.lectures.potencia')
carrega_lect_wiz_o = c.model('giscedata.lectures.pool.wizard')
wiz_ranas_o = c.model('wizard.ranas')
avancar_f_wiz_o = c.model('wizard.avancar.facturacio')
modcon_obj = c.model('giscedata.polissa.modcontractual')

polisses_inicials = [] # totes les polisses inicials
te_facturacio_suspesa = [] # te facturació suspesa
no_corregits = [] #No te abonadora de proveïdor
sense_lectures = [] #No n'hi ha lectures per esborrar
sense_factures_rectificar = [] #No tenen factures normals per rectificar
amb_f_esborrany = [] #Tenen factures normals en esborrany, cal esborrar-les?
pols_rectificades = [] #S'ha fet la Abonadora i Rectificadora
pols_avancades = [] #S'ha avançat facturació
pols_no_avancades = [] #No s'ha avançat facturació
errors = [] #Ha hagit un error inesperat al processar la polissa

def get_primera_corregir(pol_id):
    data_desde = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

    f_prov_ref = fact_obj.search([('polissa_id','=',pol_id),('type','=','in_refund'),('data_inici','>',data_desde)], order='data_inici ASC')

    for f_id in f_prov_ref:
        f = fact_obj.browse(f_id)
        f_c_id = fact_obj.search([('type','=','out_refund'),('polissa_id','=',pol_id),('data_inici','=',f.data_inici)])
        if len(f_c_id)>1:
            print "WHaaat {}".format(f_id)
        elif not f_c_id:
            return f_id
    return False

def fix_contracts_after_rectificative_F1():
    for pol_id in tqdm(polisses_inicials):
        try:
            p = pol_o.browse(pol_id)

            success("Processant polissa {}", p.name)
            if p.facturacio_suspesa:
                te_facturacio_suspesa.append(pol_id)
                step("te facturació suspesa")
                continue
            data_ultima_lectura = p.data_ultima_lectura
            ##Busquem la primera abonadora de proveidor que no te abonadora de client
            f_prov_primera = get_primera_corregir(pol_id)
            if not f_prov_primera:
                no_corregits.append(pol_id)
                step("no te abonadora de proveïdor")
                continue

            data_inici_primera = fact_obj.read(f_prov_primera, ['data_inici'])['data_inici']
            esborrar_lectures_desde = data_inici_primera
            if len(modcon_obj.search([('polissa_id','=',pol_id), ('data_inici','=',data_inici_primera)], limit=1, context={'active_test': False})) != 0:
                #Si coincideix amb l'inici d'una modcon hem de esborrar també les inicials
                esborrar_lectures_desde = (datetime.strptime(data_inici_primera, '%Y-%m-%d') - timedelta(days=1)).strftime("%Y-%m-%d")

            search_params = [
                ('name','>=',esborrar_lectures_desde),
                ('comptador.polissa', '=', pol_id),
            ]

            lects_esborrar = lect_obj.search(search_params, context={'active_test':False})
            if not lects_esborrar:
                sense_lectures.append(pol_id)
                step("no te lectures per esborrar")
                continue

            lect_obj.unlink(lects_esborrar)
            step("{} lectures esborrarades", len(lects_esborrar))

            lects_pot_esborrar = lect_pot_obj.search(search_params, context={'active_test':False})
            if lects_pot_esborrar:
                lect_pot_obj.unlink(lects_pot_esborrar)
                step("{} lectures de potencia esborrades",len(lects_pot_esborrar))
            else:
                step("no te lectures de potencia per esborrar")

            ####### carrega lectures fins data última lectura facturada
            step("carregant lectures")
            data_facturat_ok = (datetime.strptime(esborrar_lectures_desde, '%Y-%m-%d') - timedelta(days=1)).strftime("%Y-%m-%d")
            p.write({'data_ultima_lectura':data_facturat_ok})
            wiz_id = carrega_lect_wiz_o.create({'date':data_ultima_lectura},context={'model':'giscedata.polissa'})
            wiz_id.action_carrega_lectures(context={'active_id': pol_id,'active_ids':[pol_id],'model':'giscedata.polissa'})
            p.write({'data_ultima_lectura':data_ultima_lectura})
            step("lectures carregades")

            ###### AB i RE facts clients ######
            f_cli_rectificar = fact_obj.search([
                ('type','=','out_invoice'),('refund_by_id','=',False),('polissa_id','=',pol_id),
                ('data_inici','>=',data_inici_primera),('state','!=','draft')
            ])
            f_cli_rectificar_draft = fact_obj.search([
                ('type','=','out_invoice'),('refund_by_id','=',False),('polissa_id','=',pol_id),
                ('data_inici','>=',data_inici_primera),('state','=','draft')
            ])
            if f_cli_rectificar_draft:
                fact_obj.unlink(f_cli_rectificar_draft)
                amb_f_esborrany.append([pol_id, f_cli_rectificar_draft])
                step("factures en esborrany esborrades {}", len(f_cli_rectificar_draft))

            if f_cli_rectificar:
                step("abonem i rectifiquem")
                context={'active_ids':f_cli_rectificar, 'active_id':f_cli_rectificar[0]}
                wiz_id = wiz_ranas_o.create({}, context=context)
                fres_resultat = wiz_id.action_rectificar(context=context)
                pols_rectificades.append([pol_id, fres_resultat])
                step("abonat i rectificat")
            else:
                sense_factures_rectificar.append(pol_id)
                step("res per abonar i rectificar")

            ###### Avancar facturacio ##########
            step("avancem facturació")
            wiz_av_id = avancar_f_wiz_o.create({},context={'active_id':pol_id})
            data_inici_anterior = None
            pol_avancar_info = []
            while wiz_av_id.data_inici != data_inici_anterior:
                step("generem factura")

                data_inici_anterior = wiz_av_id.data_inici

                wiz_av_id.action_generar_factura()
                info = wiz_av_id.info
                if wiz_av_id.state == 'error':
                    pols_no_avancades.append([pol_id, pol_avancar_info])
                    break
                else:
                    pol_avancar_info.append(info)
                step("factura generada")
                if wiz_av_id.state != 'init': break
            pols_avancades.append([pol_id, pol_avancar_info])
            step("facturació avancada")
        except Exception as e:
            errors.append([pol_id, str(e)])
            step("Error: {}", str(e))
            traceback.print_exc(file=sys.stdout)

def output_results():
    success("Resultat final")
    success("--------------")

    success("Número de Polisses processades: {}", len(polisses_inicials))

    success("ERRORS inicials:")
    success("----------------")
    success("Te facturació suspesa: {}",len(te_facturacio_suspesa))
    step(te_facturacio_suspesa)
    success("Sense abonadora de proveidor: {}",len(no_corregits))
    step(no_corregits)
    success("Sense lectures per esborrar: {}",len(sense_lectures))
    step(sense_lectures)

    success("Abonant i rectificant factures:")
    success("-------------------------------")
    success("Sense factures normals per rectificar: {}",len(sense_factures_rectificar))
    step(sense_factures_rectificar)
    success("Tenen factures normals en esborrany, que s'han esborrat: {}",len(amb_f_esborrany))
    step(amb_f_esborrany)
    success("S'ha fet abonadora i rectificadora: {}",len(pols_rectificades))
    print_list(pols_rectificades)


    success("Avançant facturació:")
    success("--------------------")

    success("Polisses avançades: {}",len(pols_avancades))
    print_list(pols_avancades)
    success("Polisses no avançades: {}",len(pols_no_avancades))
    print_list(pols_no_avancades)


    success("----------------------------------")
    success("Errors apareguts durant el procés: {}", len(errors))
    print_list(errors)

def print_list(lst):
    for item in lst:
        pol_id = item[0]
        pol_text = item[1]
        pol_name = pol_o.read(pol_id,['name'])['name']
        step(" - id {} polissa {}", pol_id, pol_name)
        step(pol_text)

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

def read_polissa_names(csv_file):
    one_id = pol_o.search([], limit=1)[0]
    one_name = pol_o.read(one_id, ['name'])['name']
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        csv_content = [row[0].zfill(len(one_name)) for row in reader if row[0]]
    return list(set(csv_content))


def main(csv_file):
    polissa_names = read_polissa_names(csv_file)
    polisses_inicials.extend(search_polissa_by_names(polissa_names))

    fix_contracts_after_rectificative_F1()

    output_results()


if __name__=='__main__':
    parser = argparse.ArgumentParser(
            description="Reescriptura de la facturació d'una polissa"
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        required=True,
        help="csv amb el nom de les pòlisses a modificar (a la primera columna i sense capçalera)"
    )

    args = parser.parse_args()

    try:
        main(args.csv_file)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")
# vim: et ts=4 sw=4
