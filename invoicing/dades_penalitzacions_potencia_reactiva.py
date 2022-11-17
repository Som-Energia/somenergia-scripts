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
from collections import OrderedDict

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
item = OrderedDict([('Contracte',0),('Tarifa Comercialitzadora',0),('Energia activa',0),('MAG',0),('Penalització reactiva',0),
    ('Potència',0),('Excés potència',0),('Excedents',0),('Lloguer comptador',0),('IVA',0),('IESE',0),('Altres',0),('TOTAL',0)])

keys = item.keys()

pol_ids = pol_obj.search(
    [('tarifa.codi_ocsum', 'in', ['019', '020', '021', '022', '023'])])
for pol_id in pol_ids:
    item = OrderedDict([('Contracte',0),('Tarifa Comercialitzadora',0),('Energia activa',0),('MAG',0),('Penalització reactiva',0),
        ('Potència',0),('Excés potència',0),('Excedents',0),('Lloguer comptador',0),('IVA',0),('IESE',0),('Altres',0),('TOTAL',0)])

    pol = pol_obj.browse(pol_id)

    item['Contracte'] = pol.name
    item['Tarifa Comercialitzadora'] = 'Indexada' if 'indexada' in pol.llista_preu.name.lower() else 'No'

    fact_ids = fact_obj.search([('polissa_id', '=', pol_id), ('data_final', '<=', datetime.strftime(
        last_month_day, '%Y-%m-%d')), ('data_inici', '>', datetime.strftime(year_before, '%Y-%m-%d')), 
        ('type','in',['out_invoice', 'out_refund'])])

    for fact_id in fact_ids:
        fact = fact_obj.browse(fact_id)
        factor = 1.0 if fact.type == 'out_invoice' else -1.0
        for line in fact.linies_energia:
            if 'topall del gas' in line.name:
                item['MAG'] += line.price_subtotal * factor
            else:
                item['Energia activa'] += line.price_subtotal * factor
        item['Penalització reactiva'] += fact.total_reactiva * factor
        item['Potència'] += fact.total_potencia * factor
        item['Excés potència'] += fact.total_exces_potencia * factor
        item['Excedents'] += fact.total_generacio * factor
        item['Lloguer comptador'] += fact.total_lloguers * factor
        for tax_line in fact.tax_line:
            if 'IVA' in tax_line.name or 'IGIC' in tax_line.name :
                item['IVA'] += tax_line.amount * factor # IVA / IGIC
            else:
                item['IESE'] += tax_line.amount * factor
        item['Altres'] += fact.total_altres * factor
        item['TOTAL'] += fact.amount_total * factor

    item_values = item.items()
    for key,value in item_values:
        if isinstance(value, float):
            item[key] = round(value,2)

    items.append(item)

file_name = '/tmp/dades_penalitzacions_potencia_reactiva_{}_{}.csv'.format(datetime.strftime(year_before, '%Y-%m-%d'),datetime.strftime(last_month_day, '%Y-%m-%d'))
with open(file_name, 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(items)


