# -*- coding: utf-8 -*-

import sys
import psycopg2
import psycopg2.extras

import configdb
import datetime
from decimal import Decimal

## SYNTAX
# script.py ine 2015-01-01 2015-04-01

def dump_results(results):
    fields = [
            'NIF',
            'CUPS',
            'dirección',
            'ref_catastral',
            'número_factura',
            'fecha_factura',
            'fecha_inicio',
            'fecha_final',
            'emisor',
            'tipo',
            'cantidad_total_distribuidora',
            'cantidad_alquiler_distribuidora',
            'cantidad_cliente_energía',
            'cantidad_cliente_potencia',
            'cantidad_cliente_alquiler',
            'cantidad_cliente_atr',
            'tasas_eléctricas',
            'iva',
            'total']
    print ';'.join(fields)
    for items in results:
        print ';'.join(items)

class MunicipalTaxesInvoicingReport:
    def __init__(self, cursor, start_date, end_date):
        self.cursor = cursor
        self.start_date = start_date
        self.end_date = end_date

    def by_city(self, ine):
        sql = os.path.join(os.path.dirname(
              os.path.realpath(__file__)), 'sql', 'municipaltax_detailed.sql')
        with open(sql) as f:
            query = f.read()
            self.cursor.execute(query,{ 
                'start_date': self.start_date,
                'end_date': self.end_date,
                'ine': ine})

            results = []
            for x in self.cursor.fetchall():
                items = []
                for item in x:
                    if isinstance(item, datetime.date):
                        item = item.strftime('%Y-%m-%d')
                    if isinstance(item, Decimal):
                        item = float(item)
                    items.append(str(item))
                results.append(items)
            return results

ine =  sys.argv[1]
start_date =  sys.argv[2]
end_date =  sys.argv[3]

try:
    dbconn=psycopg2.connect(**configdb.psycopg)
except Exception, ex:
    print "Unable to connect to database "
    raise ex

m = MunicipalTaxesInvoicingReport(dbconn.cursor(), start_date,end_date)
dump_results(m.by_city(ine))
