#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import sys
import traceback
import configdb
from erppeek import Client
from yamlns import namespace as ns
from consolemsg import step, success, error, warn
import csv
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
pol_obj = O.GiscedataPolissa
fact_obj = O.GiscedataFacturacioFactura


today = datetime.today()

day_today = int(today.strftime("%d"))
last_month_day = today - timedelta(days=day_today)
year_before = last_month_day - relativedelta(months=12)

items = []

pol_ids = pol_obj.search(
    [('tarifa.codi_ocsum', 'in', ['019', '020', '021', '022', '023'])])
for pol_id in pol_ids:
    item = {}
    pol = pol_obj.browse(pol_id)

    item['Contracte'] = pol.name
    item['Tarifa Comercialitzadora'] = 'Indexada' if 'indexada' in pol.llista_preu.name.lower() else 'No'

    fact_ids = fact_obj.search([('polissa_id', '=', pol_id), ('data_final', '<=', datetime.strftime(
        last_month_day, '%Y-%m-%d')), ('data_inici', '>', datetime.strftime(year_before, '%Y-%m-%d')), 
        ('invoice_id.invoice_type','in',['out_invoice', 'out_refund'])])

    item['Energia activa'] = 0
    item['Penalització reactiva'] = 0
    item['Potència'] = 0
    item['Excés potència'] = 0
    item['Excedents'] = 0
    item['IVA'] = 0
    item['IESE']
    for fact_id in fact_ids:
        fact = fact_obj.browse(fact_id)
        item['Energia activa'] += fact.total_energia
        item['Penalització reactiva'] += fact.total_reactiva
        item['Potència'] += fact.total_potencia
        item['Excés potència'] += fact.total_exces_potencia
        item['Excedents'] += fact.total_generació
        item['Altres'] += fact.total_altres

        for tax_line in fact.tax_line:
            if 'IVA' in tax_line.name or 'IGIC' in tax_line.name :
                item['IVA'] = tax_line.amount # IVA / IGIC
            else:
                item['IESE'] = tax_line.amount

