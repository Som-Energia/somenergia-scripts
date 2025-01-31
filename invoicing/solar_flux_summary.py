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
from datetime import datetime, timedelta


step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
pol_obj = O.GiscedataPolissa
fact_obj = O.GiscedataFacturacioFactura
desc_obj = O.GiscedataBateriaVirtualPolissaDescompte
ir_obj = O.IrModelData
autoconsum_excedents_product_id = ir_obj.get_object_reference(
    "giscedata_facturacio_comer",
    "saldo_excedents_autoconsum"
)[1]

def search_and_add(pol_name):
    pol_name = pol_name.strip().zfill(7)
    step("Cerquem la polissa... {}", pol_name)
    found_ids = pol_obj.search(
        [('name', '=', pol_name)],
        context={'active_test': False}
    )

    if len(found_ids) != 1:
        warn("item {} ha trobat {} polisses! {}", pol_name, len(found_ids), found_ids)
        return []

    return found_ids


def search_polisses_by_name(pol_names):
    pol_ids = []
    pol_names_list = pol_names.split(',')
    step("Trobades {} noms de possibles pòlisses", len(pol_names_list))
    for pol_name in pol_names_list:
        pol_ids.extend(search_and_add(pol_name))

    step("Trobades {} pòlisses", len(pol_ids))
    return pol_ids


def get_fact_type(rectificative_type):
    if rectificative_type == 'N':
        return 'Normal'
    if rectificative_type in ['B', 'A']:
        return 'Abonadora'
    if rectificative_type == 'R':
        return 'Rectificadora'
    return rectificative_type


def get_comma(number, rectificative_type):
    if rectificative_type in ['B', 'A']:
        number = number * -1.0
    text = '{:.2f}'.format(number)
    return text.replace('.', ',')


def report_header():
    return [
        'Polissa',
        'Id factura',
        'Data Factura',
        'Numero factura',
        'Tipus',
        'Rectifica',
        'Periode inci',
        'Periode final',
        'Sols generats',
        'Dte sols aplicats']


def report_process(data):
    if 'fact' in data:
        return [
            data.fact.polissa_id.name,
            data.fact.id,
            data.fact.date_invoice,
            data.fact.number,
            get_fact_type(data.fact.rectificative_type),
            data.fact.rectifying_id.number if data.fact.rectifying_id else '',
            data.fact.data_inici,
            data.fact.data_final,
            get_comma(data.suns_generated, data.fact.rectificative_type),
            get_comma(data.flux_solar_discount, data.fact.rectificative_type),
        ]
    if 'desc' in data:
        return [
            data.pol.name,
            '',
            data.date,
            '',
            '',
            '',
            '',
            '',
            get_comma(data.impo, 'N'),
            '0,0'
        ]
    return []


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


def main(polissa_names, fitxer_csv):
    step("")
    step("cercant polisses.")
    if polissa_names:
        pol_ids = search_polisses_by_name(polissa_names)
    else:
        pol_ids = []

    step("")
    step("trobades {} pòlisses a tractar.", len(pol_ids))

    pol_id = pol_ids[0]

    fact_ids = fact_obj.search([
        ('polissa_id', '=', pol_id),
        ('type', 'in', ['out_refund', 'out_invoice']),
        ('state', 'in', ['paid', 'open']),
        ('data_inici', '>=', '2022-01-01'),
    ], order='data_inici DESC')

    step("trobades {} factures a tractar.", len(fact_ids))
    report = []
    for fact_id in tqdm(fact_ids):
        data = ns()
        report.append(data)

        fact = fact_obj.browse(fact_id)
        data['fact'] = fact

        #copied from pdf generator
        flux_solar = 0
        for line in fact.linia_ids:
            if line.tipus in ("altres", "cobrament") and line.product_id.code == "PBV":
                flux_solar += line.price_subtotal
        data["flux_solar_discount"] = flux_solar

        #copied from pdf generator
        ajustment = 0.0
        surplus_kwh = 0.0
        surplus_e = 0.0
        for l in fact.linies_generacio:  # noqa: E741
            if l.product_id.id == autoconsum_excedents_product_id:
                ajustment += l.price_subtotal
            else:
                surplus_kwh += l.quantity
                surplus_e += l.price_subtotal

        surplus_kwh = surplus_kwh * -1.0
        surplus_e = surplus_e * -1.0
        data['suns_generated'] =  ajustment * 0.80

    pol = pol_obj.browse(pol_id)
    bat = pol.bateria_ids[0]
    desc_ids = desc_obj.search([('bateria_polissa_id', '=', bat.id), ('name', 'like', '%puntual%')])
    for desc_id in tqdm(desc_ids):
        data = ns()
        report.append(data)
        desc = desc_obj.browse(desc_id)
        data['desc'] = desc
        data['pol'] = pol
        perm = desc.perm_read()
        data['date'] = perm['create_date'][:19]
        data['impo'] = desc.read(['import'])['import']

    build_repport(report, fitxer_csv)
    success("Generated file: {}", fitxer_csv)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Generador de resums per bateries virtuals'
    )

    parser.add_argument(
        '--polissa_names',
        dest='pol_names',
        help="Nom de la pólissa"
    )

    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
        )

    args = parser.parse_args()
    try:
        main(
            args.pol_names,
            args.output,
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4
