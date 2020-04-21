#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import StringIO
import csv
from yamlns import namespace as ns
from consolemsg import step, success
from validacio_eines import lazyOOOP
#from gestionatr.defs import TENEN_AUTOCONSUM, TABLA_113

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

TABLA_113 = [
    ('00', u'Sin Autoconsumo'),
    ('01', u'Autoconsumo Tipo 1'),
    ('2A', u'Autoconsumo tipo 2 (según el Art. 13. 2. a) RD 900/2015)'),
    ('2B', u'Autoconsumo tipo 2 (según el Art. 13. 2. b) RD 900/2015)'),
    ('2G', u'Servicios auxiliares de generación ligada a un autoconsumo tipo 2'),
    ('31', u'Sin Excedentes Individual – Consumo'),
    ('32', u'Sin Excedentes Colectivo – Consumo'),
    ('33', u'Sin Excedentes Colectivo con acuerdo de compensación – Consumo'),
    ('41', u'Con excedentes y compensación Individual - Consumo '),
    ('42', u'Con excedentes y compensación Colectivo– Consumo'),
    ('51', u'Con excedentes sin compensación Individual sin cto de SSAA en Red Interior– Consumo'),
    ('52', u'Con excedentes sin compensación Colectivo sin cto de SSAA en Red Interior– Consumo'),
    ('53', u'Con excedentes sin compensación Individual con cto SSAA en Red Interior– Consumo'),
    ('54', u'Con excedentes sin compensación individual con cto SSAA en Red Interior– SSAA'),
    ('55', u'Con excedentes sin compensación Colectivo/en Red Interior– Consumo'),
    ('56', u'Con excedentes sin compensación Colectivo/en Red Interior - SSAA'),
    ('61', u'Con excedentes sin compensación Individual con cto SSAA a través de red – Consumo'),
    ('62', u'Con excedentes sin compensación individual con cto SSAA a través de red – SSAA'),
    ('63', u'Con excedentes sin compensación Colectivo a través de red – Consumo'),
    ('64', u'Con excedentes sin compensación Colectivo a través de red - SSAA'),
    ('71', u'Con excedentes sin compensación Individual con cto SSAA a través de red y red interior – Consumo'),
    ('72', u'Con excedentes sin compensación individual con cto SSAA a través de red y red interior – SSAA'),
    ('73', u'Con excedentes sin compensación Colectivo con cto de SSAA  a través de red y red interior – Consumo'),
    ('74', u'Con excedentes sin compensación Colectivo con cto de SSAA a través de red y red interior - SSAA'),
]

TENEN_AUTOCONSUM = [x[0] for x in TABLA_113 if x[0] not in ['00', '01', '2A', '2B', '2G']]

TABLA_113_dic = {k: v for k, v in TABLA_113}

Obj = lazyOOOP()

pol_obj = Obj.GiscedataPolissa
fact_obj = Obj.GiscedataFacturacioFactura
line_obj = Obj.GiscedataFacturacioFacturaLinia
model_obj = Obj.IrModelData

autoconsum_excedents_product_id = model_obj.get_object_reference('giscedata_facturacio_comer', 'saldo_excedents_autoconsum')[1]

pol_ids = pol_obj.search([('autoconsumo', 'in', TENEN_AUTOCONSUM)])

auto_invoices = 0
auto_kwh = 0
auto_price = 0
auto_co_kwh = 0
auto_co_price = 0

header = [
    'Polissa',
    'Idioma del titular',
    'Email del titular',
    'Email de notificacio',
    'Codi Distri',
    'Distri',
    'Data ultima facturada (polissa)',
    'Facturacio suspesa ',
    'Estimable',
    'Tipus autoconsum',
    'Te autoconsum ass.',
    'Estat autoconsum ass.',
    'Data inici autoconsum ass.',
    'Te modcon autoconsum (polissa)',
    'Data inici modcon autoconsum (polissa)',
    'Factures generades',
    'Factures des de alta autoconsum ass. generades',
    'Factures des de alta autoconsum ass. amb linies de generacio',
    'kWh excedents',
    '€ per kWh excedents',
    'kWh excedents compensats',
    '€ per kWh excedents compensats',
    ]
report = [header]

def adapt(text):
    return type(u'')(text).encode('utf8')

def findAutoconsumModContractual(p):
    for m in p.modcontractuals_ids:
        if m.autoconsum_id or m.autoconsumo in TENEN_AUTOCONSUM:
            return m
    return None

for count, pol_id in enumerate(pol_ids):
    line = []
    pol = pol_obj.browse(pol_id)

    success("({}/{}) Polissa {}",
            count+1,
            len(pol_ids),
            pol.name)
    line.append(pol.name)

    step("Idioma titular {}",pol.titular.lang)
    line.append(pol.titular.lang)
    step("Mail Pagador {}",pol.titular.www_email)
    line.append(pol.titular.www_email)
    step("Mail notificacio contracte {}",pol.direccio_notificacio.email)
    line.append(pol.direccio_notificacio.email)

    step("Distri {}/{}",
         pol.distribuidora.ref,
         pol.distribuidora.name)
    line.extend([pol.distribuidora.ref,adapt(pol.distribuidora.name)])

    step("Data ultima lectura facturada {}",
         pol.data_ultima_lectura)
    line.append(pol.data_ultima_lectura)

    step("Facturacio suspesa {}",
         pol.facturacio_suspesa and 'Si' or 'No')
    line.append(pol.facturacio_suspesa and 'Si' or 'No')

    step("Estimació {}",
         pol.estimacio and 'No' or 'Si')
    line.append(pol.estimacio and 'No' or 'Si')

    step("Tipus autoconsum {}/{}",
         pol.autoconsumo,
         TABLA_113_dic[pol.autoconsumo])
    line.append(adapt(TABLA_113_dic[pol.autoconsumo]))

    if not pol.autoconsum_id:
        step("Dades d'autoconsum: autoconsum no actiu")
        line.extend(['No','',''])
    else:
        step("Dades d'autoconsum: autoconsum actiu , estat {}, alta {}",
             pol.autoconsum_id.state,
             pol.autoconsum_id.data_alta)
        line.extend(['Si',pol.autoconsum_id.state,pol.autoconsum_id.data_alta])

    mod = findAutoconsumModContractual(pol)
    if not mod:
        step("Dades de modificacio contractual: no trobades")
        line.extend(['No',''])
    else:
        step("Dades de modificacio contractual: data inici {}", mod.data_inici)
        line.extend(['Si',mod.data_inici])

    fact_ids = fact_obj.search([
        ('polissa_id', '=', pol.id),
        ('type', 'in', ['out_refund', 'out_invoice']),
        ])
    step("Factures totals: {}", len(fact_ids))
    line.append(len(fact_ids))

    if pol.autoconsum_id:
        fact_auto_ids = fact_obj.search([
            ('polissa_id', '=', pol.id),
            ('type', 'in', ['out_refund', 'out_invoice']),
            ('data_inici','>=',pol.autoconsum_id.data_alta),
            ])
    else:
        fact_auto_ids = []
    step("Factures des d'autoconsum totals: {}", len(fact_auto_ids))
    line.append(len(fact_auto_ids))

    if fact_auto_ids:
        fact_data = fact_obj.read(fact_auto_ids, ['linies_generacio'])
        fact_linies = [data['linies_generacio'] for data in fact_data]
    else:
        fact_linies = []

    invoices_with_lines = 0
    all_generacio_lines = []
    for fact_linia in fact_linies:
        if fact_linia:
            all_generacio_lines.extend(fact_linia)
            invoices_with_lines += 1

    step("Factures amb exedents: {}", invoices_with_lines)
    line.append(invoices_with_lines)

    quantity = 0
    price = 0
    co_quantity = 0
    co_price = 0
    if all_generacio_lines:
        all_lines_data = line_obj.read(all_generacio_lines, [
                                       'quantity',
                                       'price_subtotal',
                                       'product_id'])
        for q in all_lines_data:
            if q['product_id'][0] != autoconsum_excedents_product_id:
                quantity += q['quantity']
                price += q['price_subtotal']
            else:
                co_quantity += q['quantity']
                co_price += q['price_subtotal']

    step("kWh excedents: {}", quantity)
    step("preu per kWh excedents: {}", price)
    step("kWh excedents compensats: {}", co_quantity)
    step("preu per kWh excedents compensats: {}", co_price)

    line.extend([quantity, price, co_quantity, co_price])
    report.append(line)

    auto_invoices += invoices_with_lines
    auto_kwh += quantity
    auto_price += price
    auto_co_kwh += co_quantity
    auto_co_price += co_price

success("Finalitzat -------------------------")
success("Factures totals amb excedents: ................ {}", auto_invoices)
success("kWh excedentaris totals: ...................... {} kwh", auto_kwh)
success("Preu per kWh exedentaris totals: .............. {} €", auto_price)
success("kWh excedentaris compensats totals: ........... {} kwh", auto_co_kwh)
success("Preu per kWh exedentaris compensats totals: ... {} €", auto_co_price)

csv_doc=StringIO.StringIO()
writer_report = csv.writer(csv_doc, delimiter=';')
writer_report.writerows(report)
doc = csv_doc.getvalue()
with open(filename,'w') as f:
    f.write(doc)

# vim: et ts=4 sw=4

