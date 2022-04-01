#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64, csv
import configdb
from consolemsg import step, error, warn, fail, success
from erppeek import Client
from tqdm import tqdm


def import_f1_to_testing(f1_ids, client_from, client_to):
    f1_from_obj = client_from.model('giscedata.facturacio.importacio.linia')
    wiz_import_to_o = client_to.model('wizard.importacio.f1')

    for f1_id in tqdm(f1_ids):
        xml_data = f1_from_obj.get_xml_from_adjunt(f1_id)
        datas = base64.b64encode(xml_data.encode('utf-8'))
        filename = f1_from_obj.read(f1_id, ['name'])['name']
        wiz_id = wiz_import_to_o.create({'filename': 'copy_'+filename, 'file': datas})
        wiz_import_to_o.action_importar_f1([wiz_id.id])

def get_f1_ids(client, pol_id):
    f1_obj = client.model('giscedata.facturacio.importacio.linia')
    pol_obj = client.model('giscedata.polissa')
    cups_id = pol_obj.read(pol_id, ['cups'])['cups'][0]

    return f1_obj.search([('cups_id', '=', cups_id)])


def search_polissa_by_names(polissa_names, client):
    pol_o = client.model('giscedata.polissa')
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

def read_polissa_names(csv_file, client):
    pol_o = client.model('giscedata.polissa')
    one_id = pol_o.search([], limit=1)[0]
    one_name = pol_o.read(one_id, ['name'])['name']
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        csv_content = [row[0].zfill(len(one_name)) for row in reader if row[0]]
    return list(set(csv_content))

def main(csv_file):
    client_prod = Client(**configdb.erppeek)
    client_test = Client(**configdb.erppeek_testing)
    polissa_ids = search_polissa_by_names(read_polissa_names(csv_file, client_prod), client_prod)
    import pudb; pu.db
    total_pols_ok = 0
    for pol_id in polissa_ids:
        try:
            f1_prod_ids = get_f1_ids(
                client=client_prod, pol_id=pol_id
            )
            f1_test_ids = get_f1_ids(
                client=client_test, pol_id=pol_id
            )
            testing_not_prod = [x for x in f1_test_ids if x not in f1_prod_ids]
            if len(testing_not_prod):
                error("Per la pòlissa {} hi ha algun F1 a testing que no hi és a real: {}. No s'hi actua".format(pol_id, testing_not_prod))
                continue
            to_import_f1 = sorted([f1 for f1 in f1_prod_ids if f1 not in f1_test_ids])
            import_f1_to_testing(to_import_f1, client_prod, client_test)
            step("Importats {} F1 de la pòlissa ID {}".format(len(to_import_f1), pol_id))
            total_pols_ok +=1
        except Exception as e:
            error("Error en la pòlissa ID {}".format(pol_id))

    success("S'ha encuat la importació dels fitxers de {} pòlisses".format(total_pols_ok))

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Importar F1ns a testing')
    parser.add_argument(
        '--file',
        dest='csv_file',
        required=True,
        help="csv amb el nom de les pòlisses a modificar (a la primera columna i sense capçalera)"
    )

    return parser.parse_args()

if __name__ == '__main__':
    args=parseargs()
    if not args.csv_file:
        fail("Introdueix el fitxer amb els números de contracte")

    main(args.csv_file)
