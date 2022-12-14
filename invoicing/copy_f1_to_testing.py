#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import base64, csv
import configdb
from consolemsg import step, error, warn, fail, success
from erppeek import Client
from tqdm import tqdm


def import_f1_to_testing(f1_ids, client_from, client_to):
    f1_from_obj = client_from.model('giscedata.facturacio.importacio.linia')
    wiz_import_to_o = client_to.model('wizard.importacio.f1')

    for f1_id in tqdm(sorted(f1_ids)):
        xml_data = ''
        try:
            xml_data = f1_from_obj.get_xml_from_adjunt(f1_id)
        except Exception as e:
            f1 = f1_from_obj.browse(f1_id)
            xml_data = base64.b64decode(f1.attachment_id.datas)
        try:
            datas = base64.b64encode(xml_data.encode('utf-8'))
        except Exception as e:
            import re
            encoding = re.findall('encoding="(.*)"', xml_data)
            if encoding:
                datas = base64.b64encode(xml_data.decode(encoding[0]).encode('utf-8'))
            else:
                raise e
        filename = f1_from_obj.read(f1_id, ['name'])['name']
        wiz_id = wiz_import_to_o.create({'filename': 'copy_'+filename, 'file': datas})
        wiz_import_to_o.action_importar_f1([wiz_id.id])


def replace_att(f1_ids, client_from, client_to):
    f1_from_obj = client_from.model('giscedata.facturacio.importacio.linia')
    f1_to_obj = client_to.model('giscedata.facturacio.importacio.linia')

    for f1_id in f1_ids:
        f1_from = f1_from_obj.browse(f1_id)
        f1_to = f1_to_obj.browse(f1_id)
        f1_to.attachment_id.datas = f1_from.attachment_id.datas


def get_f1_info(client, pol_id):
    f1_obj = client.model('giscedata.facturacio.importacio.linia')
    pol_obj = client.model('giscedata.polissa')
    cups_id = pol_obj.read(pol_id, ['cups'])['cups'][0]

    f1_ids = f1_obj.search([('cups_id', '=', cups_id)])
    if not f1_ids:
        return []
    return f1_obj.read(f1_ids, ['attachment_id', 'name', 'fecha_factura_hasta'])


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

def get_f1_import_replace_att(info_from, info_to, date_from):
    f1ns_to = {x['id']: x['name'] for x in info_to}
    f1ns_from = {x['id']: x['name'] for x in info_from}
    missing = []
    for k,v in f1ns_from.items():
        if k in f1ns_to.keys():
            pass
        elif v in f1ns_to.values() or "copy_{}".format(v) in f1ns_to.values():
            pass
        else:
            missing.append(k)

    att_replace = [x['id'] for x in filter(lambda x: x['id'] in f1ns_from.keys() and x['fecha_factura_hasta']>= date_from, info_to)]
    return missing, att_replace


def copy_f1_to_testing(csv_file, date_from, polissa_name, server):
    client_prod = Client(**configdb.erppeek)
    if server == 'perp01':
        client_test = Client(**configdb.erppeek_perp01)
    else:
        client_test = Client(**configdb.erppeek_testing)
    if not csv_file:
        polissa_names = [polissa_name]
    else:
        polissa_names = read_polissa_names(csv_file, client_prod)
    polissa_ids = search_polissa_by_names(polissa_names, client_prod)
    info = []
    total_pols_ok = 0
    for pol_info in client_prod.GiscedataPolissa.read(polissa_ids, ['name']):
        pol_id = pol_info['id']
        pol_name = pol_info['name']
        try:
            f1_prod_info = get_f1_info(
                client=client_prod, pol_id=pol_id
            )
            f1_test_info = get_f1_info(
                client=client_test, pol_id=pol_id
            )
            to_import_f1, to_replace_att = get_f1_import_replace_att(f1_prod_info, f1_test_info, date_from)

            if len(f1_prod_info) < len(f1_test_info) + len(to_import_f1):
                txt = "hi ha algun F1 a testing que no hi es a real. No s'hi actua"
                error("Per la polissa {} {}".format(pol_name, txt))
                info.append({'pol':pol_name, 'info': txt})
                continue

            replace_att(to_replace_att, client_prod, client_test)
            import_f1_to_testing(to_import_f1, client_prod, client_test)
            txt = "importats {} F1 i {} adjunts actualitzats".format(len(to_import_f1), len(to_replace_att))
            step("Per la polissa {} {}".format(pol_name, txt))
            info.append({'pol':pol_name, 'info': txt})
            total_pols_ok +=1
        except Exception as e:
            error("Error en la polissa {}".format(pol_name))
            info.append({'pol':pol_name, 'info': "error inesperat"})

    success("S'ha encuat la importacio dels fitxers de {} pòlisses".format(total_pols_ok))
    return info

def write_result(result, filename):
    fieldnames = ['pol', 'info']

    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in result:
            writer.writerow({k: unicode(v).encode('utf-8') for k, v in a.items()})

def main(csv_file, output_file, from_date, server, polissa_name):
    result = copy_f1_to_testing(csv_file, from_date, polissa_name, server)
    write_result(result, output_file)

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Importar F1ns a testing')
    parser.add_argument(
        '--file',
        dest='csv_file',
        required=False,
        help="csv amb el nom de les pòlisses (a la primera columna i sense capçalera)"
    )
    parser.add_argument(
        '--polissa',
        dest='polissa_name',
        required=False,
        help="Nom de la pòlissa"
    )
    parser.add_argument(
        '--from-date',
        dest='from_date',
        required=True,
        help="Data a partir de la qual actualitzar l'adjunt dels F1 de testing"
    )
    parser.add_argument('-s', '--server',
        help="Escull un servidor destí",
    )
    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        help="Output csv file",
        )
    return parser.parse_args()

if __name__ == '__main__':
    args=parseargs()
    if not args.csv_file and not args.polissa_name:
        fail("Introdueix el fitxer amb els números de contracte o bé un número de contracte")

    main(args.csv_file, args.output, args.from_date, args.server, args.polissa_name)
