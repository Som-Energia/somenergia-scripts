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
from decimal import Decimal

periodes = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']
TOLERANCE = {
    'kWh': 1.0,
    'kW/dia': 1.0,
    'eur': Decimal("0.01"),
}

Obj = lazyOOOP()
step("Connectat al ERP")

pol_obj = Obj.GiscedataPolissa
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
    if not quantity:
        return

    if unit == 'eur':
        quantity = Decimal(str(quantity))

    key = name + period

    if key in data:
        data[key].value = data[key].value + quantity
        data[key].unit = unit
    else:
        data[key] = ns({'value': quantity, 'unit': unit})


def line_max(data, name, period, quantity, unit):
    if not quantity:
        return

    if unit == 'eur':
        quantity = Decimal(str(quantity))

    key = name + period

    if key in data:
        data[key].value = max(data[key].value, quantity)
        data[key].unit = unit
    else:
        data[key] = ns({'value': quantity, 'unit': unit})


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        '--file',
        dest='csv_file',
        help="csv amb el nom de les pòlisses per cercar les seves factures (a la primera columna i sense capçalera) requereix data --from"
    )

    parser.add_argument(
        '--polissa_names',
        dest='p_names',
        help="nùmeros de les pòlisses per cercar les seves factures (separats per comes) requereix data --from"
    )

    parser.add_argument(
        '--from',
        dest='date_from',
        help="data d'inici per cercar factures de pòlisses, obligatiori si s'especifica --file o --polissa_names"
    )

    parser.add_argument(
        '--to',
        dest='date_to',
        help="data de fi per cercar factures de pòlisses"
    )

    parser.add_argument(
        '--type',
        dest='inv_type',
        help="tipus de factures a cercar (draft) només en esborrany, (all) totes"
    )

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

    if args.csv_file and not args.date_from:
        warn("Falta data al parametre --from")
        parser.print_help()
        sys.exit()

    if args.p_names and not args.date_from:
        warn("Falta data al parametre --from")
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
            warn("Cap factura trobada amb aquest id!! {}", invoice_id)
            continue
        if len(fact_ids) > 1:
            warn("Multiples factures trobades!! {}", fact_ids)
            continue
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
            warn("Cap factura trobada amb aquest numero!! {}", invoice_number)
            continue
        if len(fact_ids) > 1:
            warn("Multiples factures trobades!! {}", fact_ids)
            continue
        ret_ids.append(fact_ids[0])
        step("Factura amb numero {} existeix {}", invoice_number, fact_ids[0])
    return ret_ids


def try_get_date(text):
    try:
        return datetime.strptime(text.strip(),'%Y-%m-%d').strftime('%Y-%m-%d')
    except Exception as e:
        return None


def get_polissa_data(csv_file):
    ret = {}

    first_id = pol_obj.search([], limit=1)[0]
    first_name = pol_obj.read(first_id, ['name'])['name']
    name_len = len(first_name)

    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)

        for row in reader:
            if not row[0]:
                continue

            pol_name = row[0].zfill(name_len)

            step("Cerquem la polissa...", pol_name)
            pol_ids = pol_obj.search([('name', '=', pol_name)],
                                     context={'active_test': False})
            if len(pol_ids) == 0:
                warn("Cap polissa trobada amb aquest nom!! {}", pol_name)
                continue
            elif len(pol_ids) > 1:
                warn("Multiples polisses trobades per {}!! IDS: {}", pol_name, pol_ids)
            else:
                step("Polissa amb nom {} existeix, ID: {}", pol_name, pol_ids[0])

            ret[pol_ids[0]] = pol_name

    return ret


def get_polissa_from_names(raw_pol_names):
    ret = {}

    first_id = pol_obj.search([], limit=1)[0]
    first_name = pol_obj.read(first_id, ['name'])['name']
    name_len = len(first_name)
    pol_names = raw_pol_names.split(',')
    for row in pol_names:
        if not row:
            continue

        pol_name = row.zfill(name_len)

        step("Cerquem la polissa...", pol_name)
        pol_ids = pol_obj.search([('name', '=', pol_name)], context={'active_test': False})
        if len(pol_ids) == 0:
            warn("Cap polissa trobada amb aquest nom!! {}", pol_name)
            continue
        elif len(pol_ids) > 1:
            warn("Multiples polisses trobades per {}!! IDS: {}", pol_name, pol_ids)
        else:
            step("Polissa amb nom {} existeix, ID: {}", pol_name, pol_ids[0])

        ret[pol_ids[0]] = pol_name

    return ret


def search_invoices_from_pol_set(pols, date_from, date_to, inv_type):
    fact_ids = []
    for pol_id in sorted(pols.keys()):
        domain = [
            ('polissa_id', '=', pol_id),
            ('type', 'in', ['out_refund', 'out_invoice']),
        ]
        if inv_type == 'draft':
            domain.append(('state', '=', 'draft'))
        if date_from:
            domain.append(('data_inici', '>=', date_from))
        if date_to:
            domain.append(('data_final', '<=', date_to))
        fact_ids.extend(fact_obj.search(domain, order='data_inici ASC'))

    return fact_ids


def search_invoices_by_csv_file(csv_file, date_from, date_to, inv_type):
    pols = get_polissa_data(csv_file)
    if not pols:
        return []
    return search_invoices_from_pol_set(pols, date_from, date_to, inv_type)


def search_invoices_by_polissa_names(pol_names, date_from, date_to, inv_type):
    pols = get_polissa_from_names(pol_names)
    if not pols:
        return []
    return search_invoices_from_pol_set(pols, date_from, date_to, inv_type)


def search_draft_invoices():
    fact_ids = fact_obj.search([
        ('state', '=', 'draft'),
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


def find_f1_in_invoice_dates_ordered_no_refactured(fact):
    f1r_ids = f1_obj.search([
        ('import_phase', '>', 30),
        ('type_factura', '=', 'R'),
        ('cups_id', '=', fact.polissa_id.cups.id),
        ('polissa_id', '=', fact.polissa_id.id),
        ('fecha_factura_desde', '>=', date_minus(fact.data_inici, 1)),
        ('fecha_factura_hasta', '<=', fact.data_final),
    ], order='fecha_factura ASC')

    domain = [
        ('import_phase', '>', 30),
        ('cups_id', '=', fact.polissa_id.cups.id),
        ('polissa_id', '=', fact.polissa_id.id),
        ('fecha_factura_desde', '>=', date_minus(fact.data_inici, 1)),
        ('fecha_factura_hasta', '<=', fact.data_final),
    ]
    if f1r_ids:
        rs = f1_obj.read(f1r_ids, ['factura_rectificada'])
        r_names = [r['factura_rectificada'] for r in rs]
        domain.append(('invoice_number_text', 'not in', r_names))

    return f1_obj.search(domain, order='fecha_factura ASC')


def get_all_f1_types(fact):
    f1_ids = f1_obj.search([
        ('cups_id', '=', fact.polissa_id.cups.id),
        ('polissa_id', '=', fact.polissa_id.id),
        ('fecha_factura_desde', '>=', date_minus(fact.data_inici, 1)),
        ('fecha_factura_hasta', '<=', fact.data_final),
    ], order='fecha_factura ASC')

    if not f1_ids:
        return ''

    f1_data = f1_obj.read(f1_ids, ['type_factura'])
    return "".join([f1['type_factura'] for f1 in reversed(f1_data)])


def find_error_f1_in_invoice_dates_ordered(fact):
    return f1_obj.search([
        ('import_phase', '<=', 30),
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


def get_f1_dates(f1_ids):
    datas = []
    for f1_id in f1_ids:
        data = f1_obj.read(f1_id, ['fecha_factura_desde', 'fecha_factura_hasta'])
        if 'fecha_factura_desde' in data and \
           data['fecha_factura_desde'] and \
           'fecha_factura_hasta' in data and \
           data['fecha_factura_hasta']:
            datas.append((data['fecha_factura_desde'], data['fecha_factura_hasta']))
    return datas


def get_next(tlist, end):
    for counter, item in enumerate(tlist):
        if item[0] == end:
            return counter
    return None


def compare_dates(fact, f1_ids, f1_error_ids):
    dates = []
    dates.extend(get_f1_dates(f1_ids))
    dates.extend(get_f1_dates(f1_error_ids))

    if not dates:
        return False, "F1's sense dates"

    if len(dates) != len(f1_ids) + len(f1_error_ids):
        return False, "Algún F1 sense dates dates {} != f1 {} + f1 err {}".format(len(dates), len(f1_ids), len(f1_error_ids))

    dates = sorted(dates)
    start = dates[0][0]
    lines = 0
    for data in dates:
        if data[0] < start:
            start = data[0]
        elif data[0] == start:
            lines += 1

    f_data_inici_1 = date_minus(fact.data_inici)
    if start != f_data_inici_1:
        return False, "Data d'inici de factura i f1s incorrectes f1 {} +1 vs fact {}, lines {}".format(start, fact.data_inici, lines)

    item = dates.pop(0)
    while dates:
        idx = get_next(dates, item[1])
        if idx is None:
            if item[1] != fact.data_final:
                return False, "Data final de factura i f1s diferents f1 {} vs fact {}, lines {}".format(item[1], fact.data_final, lines)
            lines -= 1
            idx = 0
            if dates[idx][0] != f_data_inici_1:
                return False, "Data d'inici de factura i f1s incorrectes f1 {} +1 vs fact {}, lines {}".format(dates[idx][0], fact.data_inici, lines)
        item = dates.pop(idx)

    if item[1] != fact.data_final:
        return False, "Data final de factura i f1s diferents f1 {} vs fact {}, lines {}".format(item[1], fact.data_final, lines)

    return True, "Ok"


def process_invoices(fact_ids):
    dates_error_counter = 0
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

        f1_error_ids = find_error_f1_in_invoice_dates_ordered(fact)
        data['f1_error_ids'] = f1_error_ids

        data['f1_types'] = get_all_f1_types(fact)

        ok1, error = get_and_validate_appropiate_f1(f1_ids)
        if not ok1:
            data['f1_error'] = error
            f1_error_counter += 1
            continue

        ok2, error = compare_dates(fact, f1_ids, f1_error_ids)
        if not ok2:
            data['dates_error'] = error
            dates_error_counter += 1
            continue

        f1_ids = find_f1_in_invoice_dates_ordered_no_refactured(fact)
        ok3, error = compare_invoice_consumption(fact, f1_ids)
        if not ok3:
            data['cmp_error'] = error
            compare_error_counter += 1
            continue

        if ok1 and ok2 and ok3:
            ok_counter += 1

    return report, dates_error_counter, f1_error_counter, compare_error_counter, ok_counter


def report_header():
    return [
        'id factura',
        'numero factura',
        'polissa',
        'tarifa',
        'import total',
        'data_inici',
        'data_final',
        'ok',
        'f1 trobats',
        'f1 erronis trobats',
        'tipus f1',
        'error f1',
        'error dates',
        'error consum']


def report_process(data):
    return [
        data.fact.id,
        data.fact.number,
        data.fact.polissa_id.name,
        data.fact.polissa_id.tarifa_codi,
        data.fact.amount_total,
        data.fact.data_inici,
        data.fact.data_final,
        'error' if 'f1_error' in data or 'cmp_error' in data or 'dates_error' in data else 'ok',
        len(data.f1_ids),
        len(data.f1_error_ids),
        data.get('f1_types', ''),
        data.get('f1_error', ''),
        data.get('dates_error', ''),
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
    elif args.csv_file and args.date_from:
        fact_ids.extend(search_invoices_by_csv_file(args.csv_file, args.date_from, args.date_to, args.inv_type))
    elif args.p_names and args.date_from:
        fact_ids.extend(search_invoices_by_polissa_names(args.p_names, args.date_from, args.date_to, args.inv_type))
    else:
        fact_ids.extend(search_draft_invoices())
    step("Factures trobades: {}", len(fact_ids))

    data, dat, f1, cmp, ok = process_invoices(fact_ids)
    step("Factures processades: .. {}", len(data))
    step(" Error d'f1: ........... {}", f1)
    step(" Error dates: .......... {}", dat)
    step(" Error de consums: ..... {}", cmp)
    step(" Ok: ................... {}", ok)

    repport = build_repport(data, filename)
    success("Generated file: {}", filename)

# vim: et ts=4 sw=4
