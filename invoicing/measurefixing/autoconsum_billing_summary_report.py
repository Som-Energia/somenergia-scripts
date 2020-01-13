#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from consolemsg import step, success
from validacio_eines import lazyOOOP
#from gestionatr.defs import TENEN_AUTOCONSUM, TABLA_113

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

pol_ids = pol_obj.search([('autoconsumo', 'in', TENEN_AUTOCONSUM)])

auto_invoices = 0
auto_kwh = 0
auto_price = 0


def findAutoconsumModContractual(p):
    for m in p.modcontractuals_ids:
        if m.autoconsum_id:
            return m
    return None


for count, pol_id in enumerate(pol_ids):
    pol = pol_obj.browse(pol_id)

    success("({}/{}) Polissa {}",
            count+1,
            len(pol_ids),
            pol.name)

    step("Distri {}/{}",
         pol.distribuidora.ref,
         pol.distribuidora.name)

    step("Data ultima lectura facturada {}",
         pol.data_ultima_lectura)

    step("Tipus autoconsum {}/{}",
         pol.autoconsumo,
         TABLA_113_dic[pol.autoconsumo])

    if not pol.autoconsum_id:
        step("Dades d'autoconsum: autoconsum no actiu")
    else:
        step("Dades d'autoconsum: autoconsum actiu , estat {}, alta {}",
             pol.autoconsum_id.state,
             pol.autoconsum_id.data_alta)

    mod = findAutoconsumModContractual(pol)
    if not mod:
        step("Dades de modificacio contractual: no trobades")
    else:
        step("Dades de modificacio contractual: data inici {}", mod.data_inici)

    fact_ids = fact_obj.search([
        ('polissa_id', '=', pol.id),
        ('type', 'in', ['out_refund', 'out_invoice']),
        ])
    step("Factures totals: {}", len(fact_ids))

    if fact_ids:
        fact_data = fact_obj.read(fact_ids, ['linies_generacio'])
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

    if all_generacio_lines:
        all_lines_data = line_obj.read(all_generacio_lines,
                                       ['quantity', 'price_subtotal'])
        quantity = sum([q['quantity'] for q in all_lines_data])
        price = sum([q['price_subtotal'] for q in all_lines_data])
    else:
        quantity = 0
        price = 0

    step("kWh excedents: {}", quantity)
    step("preu per kWh excedents: {}", price)

    auto_invoices += invoices_with_lines
    auto_kwh += quantity
    auto_price += price

success("Finalitzat -------------------------")
success("Factures totals amb excedents: ..... {}", auto_invoices)
success("kWh excedentaris totals: ........... {} kwh", auto_kwh)
success("Preu per kWh exedentaris totals: ... {} €", auto_price)
