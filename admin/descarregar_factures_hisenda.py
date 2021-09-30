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

## SYNTAX
# python admin/descarregar_factures_hisenda.py --start_date 2017-01-10 --end_date 2017-01-20
#
# - llibre registre IVA de factures emeses, exercicis 2017, 2018, 2019, 2020
# ha de tenir: núm. factura, data de la factura, nom del proveïdor/client, base imposable, %IVA, total € factura, NIF proveïdor/NIF client.
# num_factura; fecha_factura; nif_cliente; nombre_cliente; base_imponible; tipo_iva; total_factura
# FE000000000; 2020-01-01; 12345678A; Cognom, Nom; 1000; 21; 1210;

'''
somenergia=#
SELECT ai.number AS num_factura, ai.date_invoice AS fecha_factura, substring(rp.vat, 3) AS nif_cliente,
    rp.name AS nombre_cliente, round(ai.amount_untaxed,2) AS base_imponible, round(tax.amount *100,2) AS tipo_iva, round(ai.amount_total,2) AS total_factura

 FROM account_invoice ai
    INNER JOIN res_partner AS rp
        ON rp.id = ai.partner_id
    INNER JOIN account_invoice_tax AS invoice_tax
        ON invoice_tax.invoice_id = ai.id
    INNER JOIN account_tax AS tax
        ON invoice_tax.tax_id = tax.id

 WHERE (ai.type = 'out_invoice'
     OR ai.type = 'out_refund')
    AND ai.date_invoice >= '2020-01-01'
    AND ai.date_invoice <= '2020-01-05'
    AND tax.name like '%IVA%'
ORDER BY ai.number;


Query per treure també les factures que no porten IVA (falta pulir i pendent de confirmar que volen)
somenergia=#
SELECT ai.number AS num_factura, ai.date_invoice AS fecha_factura, rp.vat AS nif_cliente,
    rp.name AS nombre_cliente, ai.amount_untaxed AS base_imponible, tax.amount AS iva, ai.amount_total AS total_factura
 FROM account_invoice ai
    LEFT JOIN res_partner AS rp
        ON rp.id = ai.partner_id
    FULL OUTER JOIN account_invoice_tax AS invoice_tax
        ON invoice_tax.invoice_id = ai.id
    FULL OUTER JOIN account_tax AS tax
        ON invoice_tax.tax_id = tax.id  AND tax.name like '%IVA%'
    WHERE (ai.type = 'out_invoice'
        OR ai.type = 'out_refund')
    AND ai.date_invoice >= '2020-01-01'
    AND ai.date_invoice <= '2020-01-31'
    AND ai.number = 'FE2000095842';

'''
#    and ai.date_invoice >= '{0}' and ai.date_invoice <= '{1}'

FOLDER = '18f1DXG8V5QmCBKivozHldvcob6opldN1'

class MoveReport:
    def __init__(self, cursor):
        self.cursor = cursor
        pass

    def invoice_by_date(self, start_date, end_date):
        sql = '''
            SELECT ai.number AS num_factura, ai.date_invoice AS fecha_factura, substring(rp.vat, 3) AS nif_cliente,
                rp.name AS nombre_cliente, round(ai.amount_untaxed,2) AS base_imponible, round(tax.amount * 100,2) AS tipo_iva, round(ai.amount_total,2) AS total_factura

            FROM account_invoice ai
                INNER JOIN res_partner AS rp
                    ON rp.id = ai.partner_id
                INNER JOIN account_invoice_tax AS invoice_tax
                    ON invoice_tax.invoice_id = ai.id
                INNER JOIN account_tax AS tax
                    ON invoice_tax.tax_id = tax.id

            WHERE (ai.type = 'out_invoice'
                OR ai.type = 'out_refund')
                AND ai.date_invoice >= %(start_date)s::date
                AND ai.date_invoice <= %(end_date)s::date
                AND tax.name like '%%IVA%%'
            ORDER BY ai.number;
                '''
        print sql
        self.cursor.execute(sql, {'start_date': start_date, 'end_date': end_date})

        file_name = '/tmp/listado_facturas_iva_' + str(start_date[:4]) + '.csv'
        self.build_report(self.cursor.fetchall(), file_name)
        driveUtils.upload(file_name, FOLDER)
        print "From ", start_date, " to ", end_date, " exported."


    def build_report(self, records, filename):
        with codecs.open(filename,'wb','utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"')
            writer.writerow(['num_factura','fecha_factura','nif_cliente','nombre_cliente','base_imponible','tipo_iva','total_factura'])
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
    m.invoice_by_date(start_date, end_date)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='descarregar_factures_hisenda.py', description='Descarrega factures amb informació d\'IVA per hisenda i guarda al Drive.')
    parser.add_argument('-s','--start_date', help='Data inicial des de la qual es volen factures.', required=True)
    parser.add_argument('-e','--end_date', help='Data final fins la qual es volen factures.', required=True)
    args = parser.parse_args(sys.argv[1:])
    main(args)

# vim: et ts=4 sw=4

