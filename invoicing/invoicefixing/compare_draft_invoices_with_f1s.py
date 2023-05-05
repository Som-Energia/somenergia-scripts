#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import StringIO
import csv
import argparse
import sys
from datetime import datetime, timedelta
from yamlns import namespace as ns
from consolemsg import step, success, warn
from validacio_eines import lazyOOOP
from tqdm import tqdm

periodes = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
TOLERANCE = {
    'kWh': 1.0,
    'kW/dia': 1.0,
    'eur': 0.01,
}

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


def line_add(data, name, period, quantity, unit):
    key = name + period
    info = data.get(key, ns({'value': 0, 'unit': unit}))
    data[key] = info
    info.value = info.value + quantity
    info.unit = unit


def line_max(data, name, period, quantity, unit):
    key = name + period
    info = data.get(key, ns({'value': 0, 'unit': unit}))
    data[key] = info
    info.value = max(info.value, quantity)
    info.unit = unit


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        '--invoice_names',
        dest='i_names',
        help="llista de noms de les factures"
    )

    parser.add_argument(
        '--invoice_ids',
        dest='i_ids',
        help="llista d'Id de les factures"
    )

    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
        )

    args = parser.parse_args(namespace=ns())

    if bool(args.i_names) and bool(args.i_ids):
        parser.print_help()
        sys.exit()

    return args


def search_invoice_by_ids(invoice_ids):
    ret_ids = []
    invoice_ids = [int(i) for i in invoice_ids.split(',')]
    for invoice_id in invoice_ids:
        step("Cerquem la factura...", invoice_id)
        fact_ids = fact_obj.search([('id', '=', invoice_id)])
        if len(fact_ids) == 0:
            warn("Cap factura trobada amb aquest id!!")
        if len(fact_ids) > 1:
            warn("Multiples factures trobades!! {}", fact_ids)
        ret_ids.append(fact_ids[0])
        step("Factura amb ID {} existeix", fact_ids[0])
    return ret_ids


def search_invoice_by_names(invoice_numbers):
    ret_ids = []
    invoice_number_list = invoice_numbers.split(',')
    for invoice_number in invoice_number_list:
        step("Cerquem la factura...{}", invoice_number)
        fact_ids = fact_obj.search([('number', '=', invoice_number)])
        if len(fact_ids) == 0:
            warn("Cap factura trobada amb aquest numero!!")
        if len(fact_ids) > 1:
            warn("Multiples factures trobades!! {}", fact_ids)
        ret_ids.append(fact_ids[0])
        step("Factura amb numero {} existeix {}", invoice_number, fact_ids[0])
    return ret_ids


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
        ('cups_id', '=', fact.polissa_id.cups.id),
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


def extract_invoice_lines_data(fact, is_inv, data):
    for linia in fact.linia_ids:
        p = linia.name[0:2]

        if linia.tipus == 'energia':
            if p in periodes:
                line_add(data, 'energia_entrant_', p, linia.quantity, 'kWh')

        elif linia.tipus == 'generacio':
            if p in periodes:
                line_add(data, 'energia_sortint_', p, abs(linia.quantity), 'kWh')

        elif linia.tipus == 'potencia':
            if p in periodes:
                line_max(data, 'potencia_', p, linia.quantity, 'kW/dia')

        elif is_inv and linia.tipus == 'exces_potencia':
            if p in periodes:
                line_add(data, 'exces_potencia', '', linia.price_subtotal, 'eur')

        elif not is_inv and linia.tipus == 'subtotal_xml_exc':
            line_add(data, 'exces_potencia', '', linia.price_subtotal, 'eur')

        elif is_inv and linia.tipus == 'reactiva':
            if p in periodes:
                line_add(data, 'reactiva', '', linia.price_subtotal, 'eur')
        elif not is_inv and linia.tipus == 'subtotal_xml_rea':
            line_add(data, 'reactiva', '', linia.price_subtotal, 'eur')

        elif is_inv and linia.tipus == 'lloguer':
            line_add(data, 'lloguer', '', linia.price_subtotal, 'eur')

        elif not is_inv and linia.tipus == 'subtotal_xml_ren':
            line_add(data, 'lloguer', '', linia.price_subtotal, 'eur')

    return data


def extract_invoice_data(fact):
    return extract_invoice_lines_data(fact, True, ns())


def extract_f1_data(f1_ids):
    anulades = set()
    data = ns()

    for f1_id in sorted(f1_ids, reverse=True):
        f1 = f1_obj.browse(f1_id)

        if f1.type_factura == 'R':
            anulades.add(f1.codi_rectificada_anulada)

        if f1.invoice_number_text not in anulades:
            for fact in f1.liniafactura_id:
                if fact.type == 'in_invoice':
                    extract_invoice_lines_data(fact, False, data)

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

    errors = []
    for key in sorted(fa_data.keys()):

        if fa_data[key].unit != f1_data[key].unit:
            errors.append('Comparant unitats diferents {} !!, factura {} {} vs f1 {} {}'.format(key, fa_data[key].value, fa_data[key].unit, f1_data[key].value, f1_data[key].unit))

        tolerance = TOLERANCE[fa_data[key].unit]
        if abs(fa_data[key].value - f1_data[key].value) > tolerance:
            errors.append('Consum en {} excedeix la tolerancia, factura {} {} vs f1 {} {}'.format(key, fa_data[key].value, fa_data[key].unit, f1_data[key].value, f1_data[key].unit))

    if not errors:
        return True, "Ok"
    else:
        return False, "\n".join(errors)


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

    args = parse_arguments()
    filename = args.output

    fact_ids = []
    if args.i_names:
        fact_ids.extend(search_invoice_by_names(args.i_names))
    elif args.i_ids:
        fact_ids.extend(search_invoice_by_ids(args.i_ids))
    else:
        fact_ids.extend(search_draft_invoices())
    step("Factures trobades: {}", len(fact_ids))

    data, f1, cmp, ok = process_draft_invoices(fact_ids)
    step("Factures processades: .. {}", len(data))
    step(" Error d'f1: ........... {}", f1)
    step(" Error de consums: ..... {}", cmp)
    step(" Ok: ................... {}", ok)

    repport = build_repport(data, filename)
    success("Generated file: {}", filename)

# vim: et ts=4 sw=4
