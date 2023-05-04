#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import StringIO
import csv
from datetime import datetime, timedelta
from yamlns import namespace as ns
from consolemsg import step, success
from validacio_eines import lazyOOOP
from tqdm import tqdm

periodes = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
TOLERANCE = 1.0

Obj = lazyOOOP()
step("Connectat al ERP")

fact_obj = Obj.GiscedataFacturacioFactura
f1_obj = Obj.GiscedataFacturacioImportacioLinia


def date_from_str(day):
    return datetime.strptime(day, '%Y-%m-%d')


def str_from_date(day):
    return day.strftime('%Y-%m-%d')


def date_minus(day, minus_days=1):
    day = date_from_str(day)
    pre_day = day - timedelta(days=minus_days)
    return str_from_date(pre_day)


def line_add(data, name, period, quantity):
    key = name + period
    value = data.get(key, 0)
    data[key] = value + quantity

def line_max(data, name, period, quantity):
    key = name + period
    value = data.get(key, 0)
    data[key] = max(value, quantity)


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
        )
    return parser.parse_args(namespace=ns())


def search_draft_invoices():
    fact_ids = fact_obj.search([
        ('state', '=', 'draft'),
        ('tipo_rectificadora', '=', 'N'),
        ('type', 'in', ['out_refund', 'out_invoice']),
        ], order='polissa_id ASC, data_inici ASC')
    return fact_ids


def find_f1_in_invoice_dates_ordered(fact):
    return f1_obj.search([
        ('import_phase', '>', 30),
        ('polissa_id', '=', fact.polissa_id.id),
        ('fecha_factura_desde', '>=', date_minus(fact.data_inici, 1)),
        ('fecha_factura_hasta', '<=', fact.data_final),
    ], order='fecha_factura ASC')


def get_and_validate_appropiate_f1(f1_ids):
    if not f1_ids:
        return False, "Falta F1 en periode de la factura"

    if len(f1_ids) == 1:
        f1 = f1_obj.browse(f1_ids[0])
        if f1.type_factura in ('G', 'N'):
            return True, "Ok"
        else:
            return False, "Únic F1 trobat no es tipus GN: sortida no contemplada! tipus >{}<".format(f1.type_factura)
    else:
        f1 = f1_obj.browse(f1_ids[-1])
        if f1.type_factura == 'A':
            return False, "a factura emesa és per un període anul·lat."
        elif f1.type_factura in ('R', 'N', 'G'):
            return True, "Ok"
        else:
            return False, "El periode inclou un F1 de tipus no contemplat! tipus >{}<".format(f1.type_factura)

    return False, "sortida no esperada"


def extract_invoice_lines_data(fact, data):
    for linia in fact.linia_ids:
        if linia.tipus == 'energia':
            for p in periodes:
                if linia.name.startswith(p):
                    line_add(data, 'energia_entrant_', p, linia.quantity)
                    break
        elif linia.tipus == 'generacio':
            for p in periodes:
                if linia.name.startswith(p):
                    line_add(data, 'energia_sortint_', p, abs(linia.quantity))
                    break
        elif linia.tipus == 'potencia':
            for p in periodes:
                if linia.name.startswith(p):
                    line_max(data, 'potencia_', p, linia.quantity)
                    break

    return data


def extract_invoice_data(fact):
    return extract_invoice_lines_data(fact, ns())


def extract_f1_data(f1_ids):
    data = ns()
    for f1_id in f1_ids:
        f1 = f1_obj.browse(f1_id)
        for fact in f1.liniafactura_id:
            extract_invoice_lines_data(fact, data)

    return data


def compare_invoice_consumption(fact, f1_ids):
    fa_data = extract_invoice_data(fact)
    f1_data = extract_f1_data(f1_ids)

    if set(fa_data.keys()) != set(f1_data.keys()):
        text = 'Periodes incongruents!!'
        faf1 = set(fa_data.keys()) - set(f1_data.keys())
        f1fa = set(f1_data.keys()) - set(fa_data.keys())
        if faf1:
            text += " linies a la factura que no estan al f1: {}".format(",".join(sorted(faf1)))
        if f1fa:
            text += " linies al f1 que no estan a la factura: {}".format(",".join(sorted(f1fa)))

        return False, text

    for key in sorted(fa_data.keys()):
        if abs(fa_data[key] - f1_data[key]) > TOLERANCE:
            return False, 'Consum en {} excedeix la tolerancia, factura {} kWh vs f1 {} kWh'.format(key, fa_data[key], f1_data[key])

    return True, "Ok"


def process_draft_invoices(fact_ids):
    f1_error_counter = 0
    compare_error_counter = 0
    ok_counter = 0

    report = []

    for fact_id in tqdm(fact_ids):
        data = ns()
        report.append(data)

        fact = fact_obj.browse(fact_id)
        data['fact'] = fact

        f1_ids = find_f1_in_invoice_dates_ordered(fact)
        data['f1_ids'] = f1_ids

        ok, error = get_and_validate_appropiate_f1(f1_ids)
        if not ok:
            data['f1_error'] = error
            f1_error_counter += 1
            continue

        ok, error = compare_invoice_consumption(fact, f1_ids)
        if not ok:
            data['cmp_error'] = error
            compare_error_counter += 1
            continue

        ok_counter += 1

    return report, f1_error_counter, compare_error_counter, ok_counter


def report_header():
    return [
        'id factura',
        'polissa',
        'tarifa',
        'data_inici',
        'data_final',
        'ok',
        'f1 trobats',
        'error f1',
        'error consum']


def report_process(data):
    return [
        data.fact.id,
        data.fact.polissa_id.name,
        data.fact.polissa_id.tarifa_codi,
        data.fact.data_inici,
        data.fact.data_final,
        'error' if 'f1_error' in data or 'cmp_error' in data else 'ok',
        len(data.f1_ids),
        data.get('f1_error', ''),
        data.get('cmp_error', ''),
    ]


def build_repport(report, filename):
    header = report_header()

    csv_doc = StringIO.StringIO()
    writer_report = csv.writer(csv_doc, delimiter=';')
    writer_report.writerow(header)
    for data in report:
        writer_report.writerow(report_process(data))

    doc = csv_doc.getvalue()
    with open(filename, 'w') as f:
        f.write(doc)


if __name__ == '__main__':
    filename = parse_arguments().output

    fact_ids = search_draft_invoices()
    step("Factures trobades: {}", len(fact_ids))

    data, f1, cmp, ok = process_draft_invoices(fact_ids)
    step("Factures processades: .. {}", len(data))
    step(" Error d'f1: ........... {}", f1)
    step(" Error de consums: ..... {}", cmp)
    step(" Ok: ................... {}", ok)

    repport = build_repport(data, filename)
    success("Generated file: {}", filename)

# vim: et ts=4 sw=4