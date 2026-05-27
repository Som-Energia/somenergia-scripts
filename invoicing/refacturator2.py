#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import sys
import traceback
import configdb
from erppeek import Client
from yamlns import namespace as ns
from consolemsg import step, success, error, warn
from tqdm import tqdm
import csv
import StringIO


def search_invoices_by_names(c, invoice_names):
    return c.GiscedataFacturacioFactura.search([
        ('number', 'in', invoice_names.split(',')),
        ('type', 'in', ['out_invoice', 'out_refund']),
    ])


def search_invoices_by_ids(c, invoice_ids):
    return c.GiscedataFacturacioFactura.search([
        ('id', 'in', invoice_ids.split(',')),
        ('type', 'in', ['out_invoice', 'out_refund']),
    ])


def search_invoices_from_csv(c, csv_file):
    ret = []

    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)

        for row in reader:
            invoice_number = row[0].strip()
            if not invoice_number:
                continue

            step("Cerquem la factura...", invoice_number)
            invoice_ids = c.GiscedataFacturacioFactura.search([
                ('number', '=', invoice_number),
                ('type', 'in', ['out_invoice', 'out_refund']),
            ], context={'active_test': False})
            if len(invoice_ids) == 0:
                warn("Cap factura trobada amb aquest numero {}", invoice_number)
            elif len(invoice_ids) == 1:
                step("Factura trobada per {}!! ID: {}", invoice_number, invoice_ids)
                ret.extend(invoice_ids)
            else:
                warn("Multiples Factures Trobades per {}: IDS: {} --> REVISAR MANUALMENT!!", invoice_number, invoice_ids)

    return ret


def refactura(c, fact_id):
    ctx = {"active_ids": [fact_id], "active_id": fact_id}
    try:
        wiz = c.WizardRanas.create({}, context=ctx)
        fres_resultat = c.WizardRanas.action_rectificar(wiz.id, context=ctx)
    except Exception as e:
        error("Error refacturant factura ID: {} --> {}", fact_id, str(e))
        fres_resultat = []
    return fres_resultat


def report_header():
    return [
        'Factura ID',
        'Factura Numero',
        'Total Factura',
        'Polissa',
        'Refactura ID',
        'Refactura Sentit',
        'Total Refactura',
    ]


def report_process(c, fact_id, refact_id):
    fact_o = c.GiscedataFacturacioFactura
    result = [fact_id]
    fact = fact_o.browse(fact_id)
    result.append(fact.number)
    result.append(fact.amount_total)
    result.append(fact.polissa_id.name if fact.polissa_id else '')

    if refact_id:
        refa = fact_o.browse(refact_id)
        result.append(refact_id)
        result.append(refa.type)
        result.append(refa.amount_total)
    else:
        result.append('')
        result.append('')
        result.append('')

    return result


def build_report(c, refact_ids, fact_ids, csv_output):
    csv_doc = StringIO.StringIO()
    writer_report = csv.writer(csv_doc, delimiter=';')
    writer_report.writerow(report_header())
    for fact_id in fact_ids:
        if fact_id in refact_ids:
            for refact_id in refact_ids.get(fact_id, []):
                writer_report.writerow(report_process(c, fact_id, refact_id))
        else:
            writer_report.writerow(report_process(c, fact_id, None))

    doc = csv_doc.getvalue()
    with open(csv_output, 'w') as f:
        f.write(doc)


def main(invoice_names, invoice_ids, csv_file, doit, csv_output):
    if doit:
        success("Es FARAN CANVIS!")
    else:
        success("NO es faran canvis!")

    step("Connectant a l'erp")
    c = Client(**configdb.erppeek)
    step("Connectat")

    fact_ids = []
    if invoice_names:
        fact_ids.extend(search_invoices_by_names(c, invoice_names))
    if invoice_ids:
        fact_ids.extend(search_invoices_by_ids(c, invoice_ids))
    if csv_file:
        fact_ids.extend(search_invoices_from_csv(c, csv_file))

    success("S'han trobat {} factures", len(fact_ids))

    refact_ids = {}
    for fact_id in tqdm(fact_ids):
        step("Refacturant factura ID: {}", fact_id)
        if fact_id and doit:
            ids = refactura(c, fact_id)
            step(" - {} Factura generades ID: {} --> Refactura ID: {}", len(ids), fact_id, ids)
            refact_ids[fact_id] = ids

    success("S'han processat {} factures generant {} refacturacions", len(fact_ids), len(refact_ids.keys()))
    build_report(c, refact_ids, fact_ids, csv_output)


def only_one(items):
    n = 0
    for item in items:
        if bool(item):
            n += 1
    return n == 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(
            description='Script per fer refacturacions en massa'
    )

    parser.add_argument(
        '--invoice_names',
        dest='i_names',
        help="Numeros de la factures FE..."
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        help="csv amb els numeros de les factures a refacturar"
    )

    parser.add_argument(
        '--invoice_ids',
        dest='i_ids',
        help="llista d'Id de les factures"
    )

    parser.add_argument(
        '--doit',
        dest='doit',
        help="Realitzar els canvis"
    )

    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
    )

    args = parser.parse_args()

    if not only_one([args.i_names, args.i_ids, args.csv_file]):
        parser.print_help()
        sys.exit()

    try:
        main(
            args.i_names,
            args.i_ids,
            args.csv_file,
            args.doit == 'si',
            args.output
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4