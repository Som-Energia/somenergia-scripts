#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import traceback
from erppeek import Client
import configdb
import argparse
import StringIO
import sys
import csv
from consolemsg import error, step, success, warn
from yamlns import namespace as ns
from tqdm import tqdm


step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
cups_obj = O.GiscedataCupsPs
p_obj = O.ResPartner
f1_obj = O.GiscedataFacturacioImportacioLinia

def parse_arguments():
    parser = argparse.ArgumentParser(
            description='Detector de F1 tipus R que no refacturen res i ens fan perdre temps i marejen als socis (Gràcies endesa!)'
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        help="csv amb els cups a rastrejar F1 tipus R que no refacturen res"
    )

    parser.add_argument(
        '--from',
        dest='date_from',
        help="data d'inici per cercar f1 tipus R que no refacturen res"
    )

    parser.add_argument(
        '--to',
        dest='date_to',
        help="data de fi per cercar f1 tipus R que no refacturen res"
    )

    parser.add_argument(
        '--modify',
        dest='doit',
        help="Realitzar els canvis"
    )

    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
        )

    args = parser.parse_args(namespace=ns())

    if not args.date_from:
        warn("Falta data al parametre --from")
        parser.print_help()
        sys.exit()

    return args


def extract_cups_from_csv(csv_file):
    ret = []

    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)

        for row in reader:
            cups_name = row[0].strip()
            if not cups_name:
                continue

            step("Cerquem el CUPS...", cups_name)
            cups_ids = cups_obj.search([('name', 'like', "{}%".format(cups_name))],
                                        context={'active_test': False})
            if len(cups_ids) == 0:
                warn("Cap CUPS trobat amb aquest codi {}", cups_name)
                continue
            elif len(cups_ids) > 1:
                warn("Multiples CUPS trobats per {}!! IDS: {}", cups_name, cups_ids)
            else:
                step("CUPS amb codi {} existeix, ID: {}", cups_name, cups_ids[0])

            ret.extend(cups_ids)

    return ret


def get_endesa_cups_list():
    step("Cerquem tots els CUPS d'endesa...")
    evil_list = p_obj.search([('ref', '=', '0031')],context={'active_test': False})
    cups_ids = cups_obj.search([('distribuidora_id', 'in', evil_list)],
                               context={'active_test': False})
    step("Trobats {} CUPS d'endesa...", len(cups_ids))
    return cups_ids


def search_F1R_from_cups(cups_id, date_from, date_to):
    params = [
        ('type_factura', '=', 'R'),
        ('cups_id', '=', cups_id),
        ('data_carrega', '>=', date_from)
    ]
    if date_to:
        params.append(('data_carrega', '<=', date_to))
    return f1_obj.search(params,order='id ASC')


def search_rectified_invoice(f1r_id):
    f1r = f1_obj.browse(f1r_id)
    if not f1r.factura_rectificada:
        warn("F1 tipus R sense factura que rectifica!!")
        return None

    params = [
        ('invoice_number_text', '=', f1r.factura_rectificada),
        ('cups_id', '=', f1r.cups_id.id),
    ]
    ids = f1_obj.search(params)
    if len(ids) == 0:
        warn("Factura rectificada no trobada {} !!", f1r.factura_rectificada)
        return None
    if len(ids) > 1:
        warn("Factura rectificada múltiple per {} !!", f1r.factura_rectificada)
        return None
    return ids[0]


def get_name(name):
    if name == u'Lloguer equip de mesura' or name == u'Alquiler equipo de medida':
        return 'LLOG_EQ_MES'
    return name


def search_equal_line(r_line, n_lines, valid_n_lines_ids):
    name = get_name(r_line.name)
    type = r_line.tipus
    prod = r_line.uos_id.id if r_line.uos_id else None
    quant = r_line.quantity
    price = r_line.price_unit_multi
    for n_line in n_lines:
        if n_line.id not in valid_n_lines_ids:
            continue
        if n_line.quantity != quant:
            continue
        if n_line.price_unit_multi != price:
            continue
        if n_line.tipus != type:
            continue
        if get_name(n_line.name) != name:
            continue
        if prod:
            if n_line.uos_id:
                if n_line.uos_id.id != prod:
                    continue
            else:
                continue
        return n_line
    return None


def compare_f1s(f1r_id, f1n_id):
    f1r = f1_obj.browse(f1r_id)
    f1n = f1_obj.browse(f1n_id)
    step("Comparant f1 {} vs {}", f1r.name , f1n.name)

    fr = f1r.liniafactura_id[0]
    fn = f1n.liniafactura_id[0]

    if len(fr.linia_ids) != len(fn.linia_ids):
        msg = "Diferent número de linies {} vs {}".format(len(fr.linia_ids), len(fr.linia_ids)) 
        warn(msg)
        return False, msg

    to_find = set(fn.linia_ids.id)
    for line_r in fr.linia_ids:
        line_n = search_equal_line(line_r, fn.linia_ids, to_find)
        if not line_n:
            msg = "Trobada una linia diferent {},{},{},{}".format(
                    line_r.name, line_r.tipus, line_r.quantity, line_r.price_unit_multi)
            warn(msg)
            return False, msg
        to_find.remove(line_n.id)

    if to_find:
        msg = "Trobades linies a la factura origen sense contrapart a la factura rectificativa {}".format(
                ','.join([f.name for f in to_find]))
        warn(msg)
        return False, msg

    if fr.amount_total != fn.amount_total:
        msg = "Diferent Total factura {} vs {}".format(fr.amount_total, fn.amount_total)
        warn(msg)
        return False, msg

    if fr.data_inici != fn.data_inici:
        msg = "Diferent data inici factura {} vs {}".format(fr.data_inici, fn.data_inici)
        warn(msg)
        return False, msg

    if fr.data_final != fn.data_final:
        msg = "Diferent data final factura {} vs {}".format(fr.data_final, fn.data_final)
        warn(msg)
        return False, msg

    msg = "Script: No refacturar, diferència 0"
    success(msg)
    return True, msg


def is_non_reinvoicing_f1r(f1r_id):
    f1n_id = search_rectified_invoice(f1r_id)
    return compare_f1s(f1r_id, f1n_id)


def report_header():
    return [
        'CUPS',
        'F1 R',
        'Nùmero factura origen F1 R',
        'Data carrega'
        'F1 rectificat',
        'Codi factura rectificada',
        'Data desde',
        'Data fins a',
        'Missatge'
    ]


def report_process(data):
    cups_id = data[0]
    f1r_id = data[1]
    msg = data[2]

    cups_data = cups_obj.read(cups_id, ['name'])
    f1r_data = f1_obj.read(f1r_id, ['name', 'invoice_number_text', 'data_carrega', 'fecha_factura_desde', 'fecha_factura_hasta'])
    f1n_id = search_rectified_invoice(f1r_id)
    f1n_data = f1_obj.read(f1n_id, ['name', 'invoice_number_text'])
    return [
        cups_data['name'],
        f1r_data['name'],
        f1r_data['invoice_number_text'],
        f1r_data['data_carrega'],
        f1n_data['name'],
        f1n_data['invoice_number_text'],
        f1r_data['fecha_factura_desde'],
        f1r_data['fecha_factura_hasta'],
        msg,
    ]


def build_report(non_reinvoicing, reinvoicing, csv_output):
    csv_doc = StringIO.StringIO()
    writer_report = csv.writer(csv_doc, delimiter=';')
    writer_report.writerow(report_header())
    for data in non_reinvoicing:
        writer_report.writerow(report_process(data))

    doc = csv_doc.getvalue()
    with open(csv_output, 'w') as f:
        f.write(doc)


def main(csv_cups, date_from, date_to, doit, csv_ouput):
    if doit:
        success("Es FARAN CANVIS!")
    else:
        success("NO es faran canvis!")

    reivoicing = []
    non_reivoicing = []

    if csv_cups:
        cups_ids = extract_cups_from_csv(csv_cups)
    else:
        cups_ids = get_endesa_cups_list()

    step("")
    step("Trobats {} cups a examinar", len(cups_ids))

    for cups_id in tqdm(cups_ids):
        f1r_ids = search_F1R_from_cups(cups_id, date_from, date_to)
        if f1r_ids:
            cups_name = cups_obj.read(cups_id, ['name'])['name']
            step("Trobats {} F1 tipus R el CUPS {}", len(f1r_ids), cups_name)
            for f1r_id in f1r_ids:
                reinv, msg = is_non_reinvoicing_f1r(f1r_id)
                if reinv:
                    non_reivoicing.append((cups_id, f1r_id, msg))
                else:
                    reivoicing.append((cups_id, f1r_id, msg))

    build_report(non_reivoicing, reivoicing, csv_ouput)

    if doit:
        success("S'HAN FET CANVIS!")
    else:
        success("NO s'han fet canvis!")


if __name__ == '__main__':

    args = parse_arguments()
    try:
        main(
            args.csv_file,
            args.date_from,
            args.date_to,
            args.doit == 'do',
            args.output,
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4