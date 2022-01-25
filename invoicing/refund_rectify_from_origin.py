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


sense_lectures = [] #No n'hi ha lectures per esborrar
sense_factures_rectificar = [] #No tenen factures normals per rectificar
amb_f_esborrany = [] #Tenen factures normals en esborrany, cal esborrar-les?
factures_generades = [] #Factures Re i AB fetes
polisses_processades = []
errors = [] #Ha hagit un error inesperat al processar la polissa

def get_provider_invoice(origin):

    f_prov_ref = fact_obj.search([('origin','=',origin),('type','=','in_invoice')])

    if len(f_prov_ref) == 0:
        not_found.append(origin)
        return False
    return f_prov_ref[0]

def refund_rectify_by_origin(origin_list):
    for origin in tqdm(origin_list):
        try:
            fact_prov_id = get_provider_invoice(origin)
            if not fact_prov_id:
                continue
            fact_prov = fact_obj.browse(fact_prov_id)
            pol_id = fact_prov.polissa_id.id
            success("Processant origen {}, periode {} - {}", origin, fact_prov.data_inici, fact_prov.data_final)
            facts_cli_ids = fact_obj.search([
                ('polissa_id', '=', pol_id), ('type','=', 'out_invoice'),
                ('refund_by_id', '=', False), ('data_inici','<', fact_prov.data_final),
                ('data_final','>', fact_prov.data_inici)
                ], order='data_inici asc')

            f_cli_rectificar_draft = fact_obj.search([
                ('id', 'in', facts_cli_ids), ('state','=','draft')
            ])
            if f_cli_rectificar_draft:
                fact_obj.unlink(f_cli_rectificar_draft)
                amb_f_esborrany.append(fact_prov.polissa_id.name)
                step("Origen {}, factures en esborrany esborrades {}", origin, len(f_cli_rectificar_draft))
                facts_cli_ids = list(set(facts_cli_ids) - set(f_cli_rectificar_draft))

            if not facts_cli_ids:
                step("res per abonar i rectificar origen {}".format(origin))
                sense_factures_rectificar.append([origin, fact_prov.polissa_id.name])
                continue
            data_ultima_lectura = fact_prov.polissa_id.data_ultima_lectura

            ## Esborrem les lectures que hem de recarregar
            data_inici_rectificacio = fact_prov.data_inici
            data_lectura_anterior = (datetime.strptime(data_inici_rectificacio, '%Y-%m-%d') - timedelta(days=1)).strftime("%Y-%m-%d")
            data_final_rectificacio = fact_prov.data_final
            search_params = [
                ('name','>=', data_lectura_anterior),
                ('name','<=',data_final_rectificacio),
                ('comptador', 'in', fact_prov.polissa_id.comptadors.id),
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

            ####### carrega lectures de l'F1 afectat ######
            step("carregant lectures")
            pol_o.write(pol_id, {'data_ultima_lectura': data_lectura_anterior})
            wiz_id = carrega_lect_wiz_o.create({'date': data_final_rectificacio},context={'model':'giscedata.polissa'})
            wiz_id.action_carrega_lectures(context={'active_id': pol_id,'active_ids':[pol_id],'model':'giscedata.polissa'})
            pol_o.write(pol_id, {'data_ultima_lectura': data_ultima_lectura})
            step("lectures carregades")

            ###### AB i RE facts clients afectades ######

            f_cli_rectificar = facts_cli_ids

            step("abonem i rectifiquem")
            context={'active_ids':f_cli_rectificar, 'active_id':f_cli_rectificar[0]}
            wiz_id = wiz_ranas_o.create({}, context=context)
            fres_resultat = wiz_id.action_rectificar(context=context)
            factures_generades.extend([[pol_id,fact_prov.polissa_id.name, fr] for fr in fres_resultat])
            step("abonat i rectificat")
            polisses_processades.append([pol_id, origin])
        except Exception as e:
            errors.append([pol_id, str(e)])
            step("Error: {}", str(e))
            traceback.print_exc(file=sys.stdout)

def output_results(filename):
    success("Resultat final")
    success("--------------")

    success("Número de factures origen processades: {}", len(polisses_processades))

    success("ERRORS inicials:")
    success("----------------")
    success("Sense lectures per esborrar: {}",len(sense_lectures))
    step(sense_lectures)

    success("Abonant i rectificant factures:")
    success("-------------------------------")
    success("Sense factures normals per rectificar: {}",len(sense_factures_rectificar))
    [success("{},{}".format(a[0], a[1])) for a in sense_factures_rectificar]

    success("Tenen factures normals en esborrany, que s'han esborrat: {}",len(amb_f_esborrany))
    step(amb_f_esborrany)
    success("S'ha fet abonadora i rectificadora: {}",len(polisses_processades))
    print_list(polisses_processades)


    success("----------------------------------")
    success("Errors apareguts durant el procés: {}", len(errors))
    print_list(errors)

    with open(filename,'w') as f:
        f.write("Id polissa, polissa, id factura \n")
        for a in factures_generades:
            f.write("{},{},{}\n".format(*a))


def print_list(lst):
    for item in lst:
        pol_id = item[0]
        pol_text = item[1]
        pol_name = pol_o.read(pol_id,['name'])['name']
        step(" - id {} polissa {}", pol_id, pol_name)
        step(pol_text)


def read_invoices_origin(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        csv_content = [row[0] for row in reader if row[0]]
    return list(set(csv_content))


def main(csv_file, outputfile):
    invoice_origins = read_invoices_origin(csv_file)
    refund_rectify_by_origin(invoice_origins)

    output_results(outputfile)


if __name__=='__main__':
    parser = argparse.ArgumentParser(
            description="Abonar i rectificar factures client a partir d'un origen de proveïdor"
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        required=True,
        help="csv amb l'origen de les factures proveïdor (a la primera columna i sense capçalera)"
    )

    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        help="Output csv file",
        )

    args = parser.parse_args()

    try:
        main(args.csv_file, args.output)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4
