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
SELECT amb_iva.num_factura,
    amb_iva.fecha_factura,
    amb_iva.nif_cliente,
    amb_iva.nombre_cliente,
    coalesce(iese.IESE,0) as IESE,
    coalesce(amb_iva.lineas_factura_con_iva,0) as lineas_factura_con_iva,
    coalesce(donatius.linia_factura_donatius,0) as linia_factura_donatius,
    ( amb_iva.total_factura_sense_donatius + coalesce(donatius.linia_factura_donatius,0) ) as total_factura
    FROM
    (
        SELECT ai.number AS num_factura, ai.date_invoice AS fecha_factura, substring(rp.vat, 3) AS nif_cliente,
            rp.name AS nombre_cliente, round(sum(ail.price_subtotal),2) AS lineas_factura_con_iva,
            round( ai.amount_tax + round(sum(ail.price_subtotal),2), 2 ) as total_factura_sense_donatius
        FROM account_invoice ai
            INNER JOIN res_partner AS rp
                ON rp.id = ai.partner_id
            INNER JOIN account_invoice_tax AS invoice_tax
                ON invoice_tax.invoice_id = ai.id
            INNER JOIN account_tax AS tax
                ON invoice_tax.tax_id = tax.id
            INNER JOIN account_invoice_line AS ail
                ON ail.invoice_id = ai.id
        WHERE (ai.type = 'out_invoice'
            OR ai.type = 'out_refund')
            AND ai.date_invoice >= '2017-01-01'
            AND ai.date_invoice <= '2017-12-31'
            AND ail.name not like '%%Fraccionament%%'
            AND ail.name not like '%%Donatiu%%'
            AND tax.name like '%%IVA%%'
        GROUP BY ai.number, ai.date_invoice, rp.vat, rp.name, ai.amount_tax
    ) as amb_iva
    FULL JOIN
    (
        SELECT num_factura, lineas_factura_iese, IESE
        FROM(
            SELECT ai.number as num_factura, round(invoice_tax.amount, 2) AS IESE,
            round(sum(ail.price_subtotal),2) as lineas_factura_iese

            FROM account_invoice ai
                INNER JOIN res_partner AS rp
                    ON rp.id = ai.partner_id
                INNER JOIN account_invoice_tax AS invoice_tax
                    ON invoice_tax.invoice_id = ai.id
                INNER JOIN account_tax AS tax
                    ON invoice_tax.tax_id = tax.id
                INNER JOIN account_invoice_line AS ail
                    ON ail.invoice_id = ai.id

            WHERE (ai.type = 'out_invoice'
                OR ai.type = 'out_refund')
                AND ai.date_invoice >= '2017-01-01'
                AND ai.date_invoice <= '2017-12-31'
                AND ail.name not like '%%Fraccionament%%'
                AND ail.name not like '%%Donatiu%%'
                AND tax.name like '%%electricidad%%'
            GROUP BY ai.number, invoice_tax.amount
            ) as _iese
    ) as iese
     ON amb_iva.num_factura = iese.num_factura

    LEFT JOIN (
        SELECT num_factura, round( sum(coalesce(price_subtotal,0)) ,2) as linia_factura_donatius
        FROM(
            SELECT distinct(ail.id), ai.number AS num_factura, ail.price_subtotal as price_subtotal
            FROM account_invoice ai
                INNER JOIN res_partner AS rp
                    ON rp.id = ai.partner_id
                INNER JOIN account_invoice_tax AS invoice_tax
                    ON invoice_tax.invoice_id = ai.id
                INNER JOIN account_tax AS tax
                    ON invoice_tax.tax_id = tax.id
                INNER JOIN account_invoice_line AS ail
                    ON ail.invoice_id = ai.id
            WHERE (ai.type = 'out_invoice'
                OR ai.type = 'out_refund')
                AND ai.date_invoice >= '2017-01-01'
                AND ai.date_invoice <= '2017-12-31'
                AND ail.name like '%%Donatiu%%'
            GROUP BY ai.number, ail.price_subtotal, ail.id
        ) as _donatius
        GROUP BY num_factura, price_subtotal
        ) as donatius
    ON donatius.num_factura = amb_iva.num_factura
'''
#    and ai.date_invoice >= '{0}' and ai.date_invoice <= '{1}'

MAX_MOVES_LINES = 1000000
FOLDER = '18f1DXG8V5QmCBKivozHldvcob6opldN1'

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
        sql = '''
            SELECT amb_iva.num_factura,
                amb_iva.fecha_factura,
                amb_iva.nif_cliente,
                amb_iva.nombre_cliente,
                coalesce(iese.IESE,0) as IESE,
                coalesce(amb_iva.lineas_factura_con_iva,0) as lineas_factura_con_iva,
                coalesce(donatius.linia_factura_donatius,0) as linia_factura_donatius,
                ( amb_iva.total_factura_sense_donatius + coalesce(donatius.linia_factura_donatius,0) ) as total_factura
                FROM
                (
                    SELECT ai.number AS num_factura, ai.date_invoice AS fecha_factura, substring(rp.vat, 3) AS nif_cliente,
                        rp.name AS nombre_cliente, round(sum(ail.price_subtotal),2) AS lineas_factura_con_iva,
                        round( ai.amount_tax + round(sum(ail.price_subtotal),2), 2 ) as total_factura_sense_donatius
                    FROM account_invoice ai
                        INNER JOIN res_partner AS rp
                            ON rp.id = ai.partner_id
                        INNER JOIN account_invoice_tax AS invoice_tax
                            ON invoice_tax.invoice_id = ai.id
                        INNER JOIN account_tax AS tax
                            ON invoice_tax.tax_id = tax.id
                        INNER JOIN account_invoice_line AS ail
                            ON ail.invoice_id = ai.id
                    WHERE (ai.type = 'out_invoice'
                        OR ai.type = 'out_refund')
                        AND ai.date_invoice >= %(start_date)s::date
                        AND ai.date_invoice <= %(end_date)s::date
                        AND ail.name not like '%%Fraccionament%%'
                        AND ail.name not like '%%Donatiu%%'
                        AND tax.name like '%%IVA%%'
                    GROUP BY ai.number, ai.date_invoice, rp.vat, rp.name, ai.amount_tax
                ) as amb_iva
                FULL JOIN
                (
                    SELECT num_factura, lineas_factura_iese, IESE
                    FROM(
                        SELECT ai.number as num_factura, round(invoice_tax.amount, 2) AS IESE,
                        round(sum(ail.price_subtotal),2) as lineas_factura_iese

                        FROM account_invoice ai
                            INNER JOIN res_partner AS rp
                                ON rp.id = ai.partner_id
                            INNER JOIN account_invoice_tax AS invoice_tax
                                ON invoice_tax.invoice_id = ai.id
                            INNER JOIN account_tax AS tax
                                ON invoice_tax.tax_id = tax.id
                            INNER JOIN account_invoice_line AS ail
                                ON ail.invoice_id = ai.id

                        WHERE (ai.type = 'out_invoice'
                            OR ai.type = 'out_refund')
                            AND ai.date_invoice >= %(start_date)s::date
                            AND ai.date_invoice <= %(end_date)s::date
                            AND ail.name not like '%%Fraccionament%%'
                            AND ail.name not like '%%Donatiu%%'
                            AND tax.name like '%%electricidad%%'
                        GROUP BY ai.number, invoice_tax.amount
                        ) as _iese
                ) as iese
                 ON amb_iva.num_factura = iese.num_factura

                LEFT JOIN (
                    SELECT num_factura, round( sum(coalesce(price_subtotal,0)) ,2) as linia_factura_donatius
                    FROM(
                        SELECT distinct(ail.id), ai.number AS num_factura, ail.price_subtotal as price_subtotal
                        FROM account_invoice ai
                            INNER JOIN res_partner AS rp
                                ON rp.id = ai.partner_id
                            INNER JOIN account_invoice_tax AS invoice_tax
                                ON invoice_tax.invoice_id = ai.id
                            INNER JOIN account_tax AS tax
                                ON invoice_tax.tax_id = tax.id
                            INNER JOIN account_invoice_line AS ail
                                ON ail.invoice_id = ai.id
                        WHERE (ai.type = 'out_invoice'
                            OR ai.type = 'out_refund')
                            AND ai.date_invoice >= %(start_date)s::date
                            AND ai.date_invoice <= %(end_date)s::date
                            AND ail.name like '%%Donatiu%%'
                        GROUP BY ai.number, ail.price_subtotal, ail.id
                    ) as _donatius
                    GROUP BY num_factura, price_subtotal
                    ) as donatius
                ON donatius.num_factura = amb_iva.num_factura
                ORDER BY amb_iva.num_factura
                OFFSET %(start_line)s LIMIT %(MAX_MOVES_LINES)s
                '''
        print sql
        self.cursor.execute(sql, {'start_date': start_date, 'end_date': end_date,
            'start_line': start_line, 'MAX_MOVES_LINES': MAX_MOVES_LINES})

        file_name = '/tmp/listado_facturas_iva_' + str(start_date[:4]) + '_' + str(start_line) + '.csv'
        self.build_report(self.cursor.fetchall(), file_name)
        driveUtils.upload(file_name, FOLDER)
        print "From ", start_date, " to ", end_date, " exported."


    def build_report(self, records, filename):
        with codecs.open(filename,'wb','utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"')
            writer.writerow(['num_factura','fecha_factura','nif_cliente','nombre_cliente','IESE','lineas_factura_con_iva','linia_factura_donatius','total_factura'])
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
    parser = argparse.ArgumentParser(prog='descarregar_factures_hisenda.py', description='Descarrega factures amb informació d\'IVA per hisenda i guarda al Drive.')
    parser.add_argument('-s','--start_date', help='Data inicial des de la qual es volen factures.', required=True)
    parser.add_argument('-e','--end_date', help='Data final fins la qual es volen factures.', required=True)
    args = parser.parse_args(sys.argv[1:])
    main(args)

# vim: et ts=4 sw=4

