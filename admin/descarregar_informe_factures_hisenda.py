# -*- coding: utf-8 -*-
import sys
import psycopg2
import psycopg2.extras
import csv
import configdb
import codecs
import driveUtils
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
#import locale
#locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
import argparse
from tqdm import tqdm
import os

## SYNTAX
# python admin/descarregar_factures_hisenda.py --start_date 2017-01-10 --end_date 2017-01-20
#
# - llibre registre IVA de factures emeses, exercicis 2017, 2018, 2019, 2020
# ha de tenir: núm. factura, data de la factura, nom del proveïdor/client, base imposable, %IVA, total € factura, NIF proveïdor/NIF client.
# num_factura; fecha_factura; nif_cliente; nombre_cliente; base_imponible; tipo_iva; total_factura
# FE000000000; 2020-01-01; 12345678A; Cognom, Nom; 1000; 21; 1210;

MAX_MOVES_LINES = 400000
FOLDER = '1CQvIZCZ3Urqr01ZLKdtcUioh2pjMa-jZ'

class MoveReport:
    def __init__(self, cursor):
        self.cursor = cursor
        pass

    def count_moves_of_year(self, start_date, end_date):
        sql = '''
                SELECT count(*)
                    FROM account_invoice AS ai
            WHERE ai.date_invoice >= '{0}'
                AND ai.date_invoice <= '{1}'
                AND (ai.type = 'out_invoice'
                OR ai.type = 'out_refund')
            '''.format(start_date, end_date)

        self.cursor.execute(sql, {'start_date': start_date,
                                  'end_date': end_date})
        result = self.cursor.fetchone()

        return int(result[0])

    def invoice_by_date(self, start_date, end_date, start_line, end_line):
        sql = os.path.join(os.path.dirname(
              os.path.realpath(__file__)), 'sql', 'informe_factures_hisenda.sql')
        with open(sql) as f:
            query = f.read()
            print query
            self.cursor.execute(query, {'start_date': start_date, 'end_date': end_date,
                'start_line': start_line, 'MAX_MOVES_LINES': MAX_MOVES_LINES})

        file_name = '/tmp/informe_hacienda_listado_facturas_iva_' + str(start_date[:4]) + '_' + str(start_line) + '.csv'
        self.build_report(self.cursor.fetchall(), file_name)
        driveUtils.upload(file_name, FOLDER)
        print "From ", start_date, " to ", end_date, " exported."


    def build_report(self, records, filename):
        with codecs.open(filename,'wb','utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"')
            writer.writerow(['factura','cups','nombre_cliente','vat_nif','fecha_factura','fecha_inicio','fecha_final','provincia','importe_potencia_sin_descuento','importe_energia_sin_descuento','importe_generacio','importe_reactiva','importe_exceso_potencia','otros_sin_iva','otros_con_iva','importe_alquiler','otras_linias_facturas_no_energia_con_iva','otras_linias_facturas_no_energia_sin_iva','otros_cobros','base_iese','cuota_iese','base_iva','cuota_iva','tipo_iva','total_factura'])
            for record in tqdm(records):
                writer.writerow(record)


def main(args):
    reload(sys)
    sys.setdefaultencoding('utf8')

    start_date =  args.start_date
    end_date = args.end_date

    try:
        dbconn=psycopg2.connect(**configdb.psycopg)
        dbconn.set_client_encoding('UTF8')
    except Exception, ex:
        print "Unable to connect to database "
        raise ex

    m = MoveReport(dbconn.cursor())
    lines = m.count_moves_of_year(start_date, end_date)
    start_line = 0
    end_line = 0

    while start_line < lines:
        end_line = start_line + MAX_MOVES_LINES
        m.invoice_by_date(start_date, end_date, start_line, end_line)
        start_line = end_line + 1



if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='descarregar_informe_hisenda_factures.py', description='Descarrega factures amb informació d\'IVA per hisenda i guarda al Drive.')
    parser.add_argument('-s','--start_date', help='Data inicial des de la qual es volen factures.', required=True)
    parser.add_argument('-e','--end_date', help='Data final fins la qual es volen factures.', required=True)
    args = parser.parse_args(sys.argv[1:])
    main(args)

# vim: et ts=4 sw=4

