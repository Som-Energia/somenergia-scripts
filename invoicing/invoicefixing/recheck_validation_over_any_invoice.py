#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import StringIO
import csv
import argparse
import sys
from yamlns import namespace as ns
from datetime import timedelta, datetime
from consolemsg import step, success, warn
from validacio_eines import lazyOOOP
from tqdm import tqdm

Obj = lazyOOOP()
step("Connectat al ERP")

pol_obj = Obj.GiscedataPolissa
fact_obj = Obj.GiscedataFacturacioFactura
f1_obj = Obj.GiscedataFacturacioImportacioLinia
val_obj = Obj.GiscedataFacturacioValidationWarningTemplate
v_obj = Obj.GiscedataFacturacioValidationValidator


def date_from_str(day):
    return datetime.strptime(day, '%Y-%m-%d')


def str_from_date(day):
    return day.strftime('%Y-%m-%d')


def date_minus(day, minus_days=1):
    day = date_from_str(day)
    pre_day = day - timedelta(days=minus_days)
    return str_from_date(pre_day)


# ----------------
# Parameters Block
# ----------------
def search_validation(validation_code):
    ids = val_obj.search([('code', 'ilike', "%"+validation_code+"%")],
                         context={'active_test': False})
    if len(ids) != 1:
        return None
    val_data = val_obj.read(ids[0], ['code', 'observation', 'parameters'])
    return val_data


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
        '--validation',
        dest='val_code',
        help="codi de la validació de factura a passar",
    )

    parser.add_argument(
        '--stored',
        dest='stored',
        help="creques pre-guardades",
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

    if not args.val_code:
        warn("Falta data al parametre --validation")
        parser.print_help()
        sys.exit()

    if not search_validation(args.val_code):
        warn("No es troba cap validació amb el codi del paràmetre --validation")
        parser.print_help()
        sys.exit()

    return args


# -----------------------
# invoice search funcions
# -----------------------
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


def search_invoices_from_pol_set(pols, date_from, date_to, inv_type):
    fact_ids = []
    for pol_id in sorted(pols):
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


def search_invoices_by_csv_file(csv_file, date_from, date_to, inv_type):
    pols = get_polissa_data(csv_file)
    if not pols:
        return []
    return search_invoices_from_pol_set(pols.keys(), date_from, date_to, inv_type)


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


def search_invoices_by_polissa_names(pol_names, date_from, date_to, inv_type):
    pols = get_polissa_from_names(pol_names)
    if not pols:
        return []
    return search_invoices_from_pol_set(pols.keys(), date_from, date_to, inv_type)


def search_invoices_stored(stored, date_from, date_to, inv_type):
    pols = []
    if stored == 'auto1':
        pols = pol_obj.search([('autoconsumo', '!=', '00')])
    if not pols:
        return []
    return search_invoices_from_pol_set(pols, date_from, date_to, inv_type)


def search_draft_invoices():
    fact_ids = fact_obj.search([
        ('state', '=', 'draft'),
        ('type', 'in', ['out_refund', 'out_invoice']),
        ], order='polissa_id ASC, data_inici ASC')
    return fact_ids


# ------------------------
# invoice process funcions
# ------------------------
def get_all_f1_data(fact):
    result = []

    f1_ids = f1_obj.search([
        ('cups_id', '=', fact.polissa_id.cups.id),
        ('polissa_id', '=', fact.polissa_id.id),
        ('fecha_factura_desde', '>=', date_minus(fact.data_inici, 1)),
        ('fecha_factura_hasta', '<=', fact.data_final),
    ], order='fecha_factura ASC')

    if not f1_ids:
        return result

    f1_data = f1_obj.read(f1_ids, ['type_factura', 'import_phase', 'invoice_number_text'])
    return f1_data


def process_invoices(fact_ids, validation_id):
    validacio_ok = 0
    validacio_err = 0
    report = []

    for fact_id in tqdm(fact_ids):

        val_result = v_obj.validate_one_invoice(fact_id, validation_id)
        if not val_result['validation_warning']:
            validacio_ok += 1
            continue

        validacio_err += 1
        data = ns()
        report.append(data)
        data['val'] = val_result
        fact = fact_obj.browse(fact_id)
        data['fact'] = fact
        data['f1s'] = get_all_f1_data(fact)

    return report, validacio_ok, validacio_err


# ---------------
# report funcions
# ---------------
def report_header():
    return [
        'id factura',
        'numero factura',
        'polissa',
        'tarifa',
        'import total',
        'data_inici',
        'data_final',
        'numero de f1 trobats',
        'tipus de factures',
        'fases',
        'Num factura origen del F1',
        'error validacio',
    ]


def report_process(data):
    return [
        data.fact.id,
        data.fact.number,
        data.fact.polissa_id.name,
        data.fact.polissa_id.tarifa_codi,
        data.fact.amount_total if data.fact.type == 'out_invoice' else data.fact.amount_total * -1.0,
        data.fact.data_inici,
        data.fact.data_final,
        len(data.f1s),
        ', '.join([f1['type_factura'] for f1 in data.f1s]),
        ', '.join([str(f1['import_phase']) for f1 in data.f1s]),
        ', '.join([f1['invoice_number_text'] for f1 in data.f1s]),
        data.val['message'].encode('utf-8'),
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


# ---------
# Main call
# ---------
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
    elif args.stored and args.stored != 'none':
        fact_ids.extend(search_invoices_stored(args.stored, args.date_from, args.date_to, args.inv_type))
    else:
        fact_ids.extend(search_draft_invoices())
    step("Factures trobades: {}", len(fact_ids))

    val_data = search_validation(args.val_code)
    step("Validacio trobada: {} {}", val_data['code'], val_data['observation'])
    step("Paràmetres de la validació: {}", val_data['parameters'])

    data, v_ok, v_error = process_invoices(fact_ids, val_data['id'])
    step("Factures processades: ....... {}", len(fact_ids))
    step(" Validacio sense error: ..... {}", v_ok)
    step(" Validacio amb  error: ...... {}", v_error)

    repport = build_repport(data, filename)
    success("Generated file: {}", filename)

# vim: et ts=4 sw=4
