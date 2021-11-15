#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from consolemsg import step, success, error, warn
from yamlns import namespace as ns
import StringIO
import csv

_states_selection = [
    ('erroni', 'Error en la importació'),
    ('valid', 'Importat correctament'),
    ('incident', 'Incidents en la importació'),
]
states_selection = dict(_states_selection)

_IMPORT_PHASES = [
    (10, '1 - Càrrega de l\'XML'),
    (20, '2 - Creació Factura'),
    (30, '3 - Validació dades'),
    (40, '4 - Càrrega de dades'),
    (50, '5 - Gestionat manualment'),
]
IMPORT_PHASES = dict(_IMPORT_PHASES)
orderedHeaders = [
    'origin',
    'type_factura',
    'data_carrega',
    'fase',
    'cups_text',
    'data_lectura_desde',
    'data_lectura_actual',
    'periode_polissa',
    'cups_polissa',
    'data_ultima_lect',
    'f_suspesa',
    'obs_suspesa',
    'polissa',
    'other_pols',
]
headers = {
    'origin': 'Numero Factura Origen',
    'type_factura': 'Tipus de Factura',
    'data_carrega': 'Data Carrega',
    'fase':  'Fase de Carrega',
    'cups_text': 'F1 CUPS',
    'data_lectura_desde': 'Data Lectura Inicial F1',
    'data_lectura_actual': 'Data Lectura Actual F1',
    'periode_polissa': 'Contracte vinculat periode',
    'cups_polissa': 'CUPS',
    'data_ultima_lect': 'Data Ultima Lectura facturada Polissa',
    'f_suspesa': 'Facturacio suspesa',
    'obs_suspesa': 'Observacions facturacio susp.',
    'polissa': 'Contracte vinculat actualment',
    'other_pols': 'Contractes vinculats historic',
}

def acc_min(acc,dat):
    if acc and dat:
        return min(acc,dat)
    if acc:
        return acc
    if dat:
        return dat
    return None

def acc_max(acc,dat):
    if acc and dat:
        return max(acc,dat)
    if acc:
        return acc
    if dat:
        return dat
    return None

def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        help="Output csv file",
        )
    parser.add_argument(
        '--start_date',
        dest='start_date',
        help='Data inicial des de la qual es volen llistar F1 amb error.')
    return parser.parse_args(namespace=ns())

filename = parseArguments().output
start_date = parseArguments().start_date

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

f1_obj = O.GiscedataFacturacioImportacioLinia
pol_obj = O.GiscedataPolissa

step("Cercant F1's")
f1_ids = f1_obj.search([
    ("data_carrega",">=",start_date),
    ("state","=","erroni"),
    ('import_phase', '!=', 10)
    ])
step("Trobats {} F1's",len(f1_ids))

#f1_ids = f1_ids[128+115:]

report = []
for counter, f1_id in enumerate(f1_ids):
    data = {}
    report.append(data)

    f1 = f1_obj.browse(f1_id)

    success("{}/{} llegint f1 {}",counter+1, len(f1_ids), f1.name)
    data['origin'] = f1.invoice_number_text
    data['type_factura'] = f1.type_factura
    data['data_carrega'] = f1.data_carrega
    data['fase'] = IMPORT_PHASES.get(f1.import_phase,"Not found error")
    data['cups_text'] = f1.cups_text
    if f1.cups_id:
        data['polissa'] = f1.cups_id.polissa_polissa.name if f1.cups_id.polissa_polissa else "Cups sense pòlissa!"
    else:
        data['polissa'] = "F1 sense cups amb pòlissa activa!"
    pol_ids = pol_obj.search([("cups.name","ilike",f1.cups_text[:20])], context={"active_test":False})
    pol_datas = pol_obj.read(pol_ids,['name','data_alta','data_baixa', 'cups'])
    old_pols = ', '.join([p['name'] for p in pol_datas])
    data['other_pols'] = old_pols

    data_lectura_desde = None
    data_lectura_actual = None
    for imp_lect in f1.importacio_lectures_ids:
        data_lectura_desde = acc_min(data_lectura_desde, imp_lect.fecha_desde)
        data_lectura_actual = acc_max(data_lectura_actual, imp_lect.fecha_actual)

    pol_name = None
    pol_id = None
    pol_cups = ''

    if len(pol_ids) == 1:
        pol_name = pol_datas[0]['name']
        pol_id = pol_datas[0]['id']
        pol_cups = pol_datas[0]['cups'][1]
    elif data_lectura_desde and data_lectura_actual:
        for pol_data in pol_datas:
            if pol_data['data_baixa']:
                if pol_data['data_alta'] < data_lectura_desde and data_lectura_actual < pol_data['data_baixa']:
                    pol_name = pol_data['name']
                    pol_id = pol_data['id']
                    pol_cups = pol_data['cups'][1]
            else:
                if pol_data['data_alta'] < data_lectura_desde:
                    pol_name = pol_data['name']
                    pol_cups = pol_data['cups'][1]
                    pol_id = pol_data['id']
    else:
        pol_name = 'no tenim dates del f1'
        pol_cups = 'no tenim dates del f1'
    data['periode_polissa'] = pol_name
    data['cups_polissa'] = pol_cups

    pol_data_ultima_lectura = 'Error'
    if pol_id:
        pol_data = pol_obj.read(pol_id,['data_ultima_lectura', 'facturacio_suspesa','observacio_suspesa'])
        pol_data_ultima_lectura = pol_data['data_ultima_lectura']
        pol_fact_suspesa = pol_data['facturacio_suspesa']
        pol_observacio_suspesa = pol_data['observacio_suspesa']
    elif f1.cups_id and f1.cups_id.polissa_polissa:
        pol_data_ultima_lectura = f1.cups_id.polissa_polissa.data_ultima_lectura
        pol_fact_suspesa = f1.cups_id.polissa_polissa.facturacio_suspesa
        pol_observacio_suspesa = f1.cups_id.polissa_polissa.f1.cups_id.polissa_polissa

    data['data_lectura_desde'] = data_lectura_desde if data_lectura_desde else "No lectures"
    data['data_lectura_actual'] = data_lectura_actual if data_lectura_actual else "No lectures"
    data['data_ultima_lect'] = pol_data_ultima_lectura
    data['f_suspesa'] = pol_fact_suspesa
    data['obs_suspesa'] = pol_observacio_suspesa
    print data.keys()

csv_doc = StringIO.StringIO()
writer_report = csv.DictWriter(csv_doc, fieldnames=orderedHeaders, delimiter=';')
writer_report.writerow(headers)
writer_report.writerows(report)
doc = csv_doc.getvalue()
with open(filename, 'w') as f:
    f.write(doc)

# vim: et ts=4 sw=4
