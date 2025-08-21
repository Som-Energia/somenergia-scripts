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
    (10, '1 - Càrrega XML'),
    (20, '2 - Creació Factura'),
    (30, '3 - Validació dades'),
    (40, '4 - Càrrega de dades'),
    (50, '5 - Gestionat manualment'),
]
IMPORT_PHASES = dict(_IMPORT_PHASES)

header = [
    'Numero Factura Origen',
    'Tipus de Factura',
    'Data Carrega',
    'Estat',
    'Fase de Carrega',
    'F1 CUPS',
    'Contracte vinculat actualment',
    'Contractes vinculats historic',
    'Contracte vinculat periode',
    'Data Lectura Inicial F1',
    'Data Lectura Actual F1',
    'Data Ultima Lectura facturada Polissa',
    'Cal refacturar',
    ]

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
        'output',
        type=str,
        help="Output csv file",
        )
    return parser.parse_args(namespace=ns())

filename = parseArguments().output

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

f1_obj = O.GiscedataFacturacioImportacioLinia
pol_obj = O.GiscedataPolissa 

step("Cercant F1's")
f1_ids = f1_obj.search([
    ("data_carrega",">=","2021-08-01"),
    ("cups_text","like","ES0031%"),
    ("type_factura","=","R")
    ])
step("Trobats {} F1's",len(f1_ids))

#f1_ids = f1_ids[128+115:]


report = [header]
for counter, f1_id in enumerate(f1_ids):
    data = []
    report.append(data)

    f1 = f1_obj.browse(f1_id)

    success("{}/{} llegint f1 {}",counter+1, len(f1_ids), f1.name)
    data.append(f1.invoice_number_text)
    data.append(f1.type_factura)
    data.append(f1.data_carrega)
    data.append(states_selection.get(f1.state,"Not found error"))
    data.append(IMPORT_PHASES.get(f1.import_phase,"Not found error"))
    data.append(f1.cups_text)
    if f1.cups_id:
        if f1.cups_id.polissa_polissa:
            data.append(f1.cups_id.polissa_polissa.name)
        else:
            data.append("Cups sense polissa!")
    else:
        data.append("F1 sense cups!")
    pol_ids = pol_obj.search([("cups","=",f1.cups_text)], context={"active_test":False})
    pol_datas = pol_obj.read(pol_ids,['name','data_alta','data_baixa'])
    old_pols = ', '.join([p['name'] for p in pol_datas])
    data.append(old_pols)

    data_lectura_desde = None
    data_lectura_actual = None
    for imp_lect in f1.importacio_lectures_ids:
        data_lectura_desde = acc_min(data_lectura_desde, imp_lect.fecha_desde)
        data_lectura_actual = acc_max(data_lectura_actual, imp_lect.fecha_actual)

    pol_name = None
    pol_id = None
    if len(pol_ids) == 1:
        pol_name = pol_datas[0]['name']
        pol_id = pol_datas[0]['id']
    elif data_lectura_desde and data_lectura_actual:
        for pol_data in pol_datas:
            if pol_data['data_baixa']:
                if pol_data['data_alta'] < data_lectura_desde and data_lectura_actual < pol_data['data_baixa']:
                    pol_name = pol_data['name']
                    pol_id = pol_data['id']
            else:
                if pol_data['data_alta'] < data_lectura_desde:
                    pol_name = pol_data['name']
                    pol_id = pol_data['id']
    else:
        pol_name = 'no tenim dates del f1'
    data.append(pol_name)

    pol_data_ultima_lectura = 'Error'
    if pol_id:
        pol_data = pol_obj.read(pol_id,['data_ultima_lectura'])
        pol_data_ultima_lectura = pol_data['data_ultima_lectura']
    elif f1.cups_id and f1.cups_id.polissa_polissa:
        pol_data_ultima_lectura = f1.cups_id.polissa_polissa.data_ultima_lectura

    data.append(data_lectura_desde if data_lectura_desde else "No lectures")
    data.append(data_lectura_actual if data_lectura_actual else "No lectures")
    data.append(pol_data_ultima_lectura)

    if pol_data_ultima_lectura == 'Error':
        data.append("error")
    elif not pol_data_ultima_lectura:
        data.append("no")
    elif data_lectura_actual:
        if data_lectura_actual <= pol_data_ultima_lectura:
            data.append("refacturar")
        else:
            data.append("no")
    else:
        data.append("no tenim data del f1")

csv_doc = StringIO.StringIO()
writer_report = csv.writer(csv_doc, delimiter=';')
writer_report.writerows(report)
doc = csv_doc.getvalue()
with open(filename, 'w') as f:
    f.write(doc)

# vim: et ts=4 sw=4
