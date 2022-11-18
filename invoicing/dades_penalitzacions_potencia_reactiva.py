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
from tqdm import tqdm
import pandas as pd

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
pol_obj = O.GiscedataPolissa
fact_obj = O.GiscedataFacturacioFactura

items = []
item = OrderedDict([('Contracte',0),('Tarifa Comercialitzadora',0),('Indexada', 0),('Energia activa',0),('MAG',0),('Penalització reactiva',0),
    ('Potència',0),('Excés potència',0),('Excedents',0),('Lloguer comptador',0),('IVA',0),('IGIC', 0),('IESE',0),('Altres',0),('TOTAL',0)])


keys = item.keys()

def output_results(from_date, to_date):
    success("Resultat final")
    success("----------------")
    success("Total de contectes tractacts: {}",len(items))
    success("Entre els dies: {} - {}", from_date, to_date)


def write_results(filename):
    """
    df = pd.DataFrame(llistat, columns=headers)
    with pd.ExcelWriter(
        "output.xlsx",
    ) as writer:
        df.to_excel(writer)
    """
    with open(filename, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
        dict_writer.writeheader()
        dict_writer.writerows(items)

def find_invoices(from_date, to_date):
    pol_ids = pol_obj.search(
        [('tarifa.codi_ocsum', 'in', ['019', '020', '021', '022', '023'])])
    for pol_id in tqdm(pol_ids[0:1]):
        item = OrderedDict([('Contracte',0),('Tarifa Comercialitzadora',0),('Indexada', 0),('Energia activa',0),('MAG',0),('Penalització reactiva',0),
            ('Potència',0),('Excés potència',0),('Excedents',0),('Lloguer comptador',0),('IVA',0),('IGIC', 0),('IESE',0),('Altres',0),('TOTAL',0)])

        pol = pol_obj.browse(pol_id)

        item['Contracte'] = pol.name
        item['Tarifa Comercialitzadora'] = pol.llista_preu.name.lower()
        item['Indexada'] = 'Indexada' if 'indexada' in pol.llista_preu.name.lower() else 'No'

        fact_ids = fact_obj.search([('polissa_id', '=', pol_id), ('data_inici', '>', from_date), ('data_final', '<=', to_date),
            ('type','in',['out_invoice', 'out_refund']), ('state','!=','draft')])

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
                    item['IVA'] += tax_line.amount * factor
                elif 'IGIC' in tax_line.name:
                    item['IGIC'] += tax_line.amount * factor
                else:
                    item['IESE'] += tax_line.amount * factor
            item['Altres'] += fact.total_altres * factor
            item['TOTAL'] += fact.amount_total * factor

        item_values = item.items()
        for key,value in item_values:
            if isinstance(value, float):
                item[key] = round(value,2)

        items.append(item)

def get_dates():

    today = datetime.today()

    day_today = int(today.strftime("%d"))
    last_month_day = today - timedelta(days=day_today)
    year_before = last_month_day - relativedelta(months=12)

    to_date = datetime.strftime(last_month_day, '%Y-%m-%d')
    from_date = datetime.strftime(year_before, '%Y-%m-%d')

    return from_date, to_date

def main(filename='output.csv'):

    from_date, to_date = get_dates()

    find_invoices(from_date, to_date)
    output_results(from_date, to_date)
    write_results(filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatische Kunde Profile erstellen'
    )

    parser.add_argument(
        '--to-date',
        dest='to_date',
        required=True,
        help="Data a partir de la qual es calcularà l'any enrera (per defecte es considera el dia d'avui i es calcularà l'últim dia del mès passat)"
    )

    parser.add_argument(
        '--output',
        dest='output',
        type=str,
        help="Output csv file",
        )
    args = parser.parse_args()

    try:
        main(args.to_date, args.output)
    except (KeyboardInterrupt, SystemExit, SystemError):
        warn("Aarrggghh you kill me :(")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Chao!")
