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
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
import argparse
from tqdm import tqdm

## SYNTAX
# python admin/descarregar_contractes_hisenda.py --start_date 2018-01-10 --end_date 2018-01-20
#
# - llistat comptadors (CUPS?) separats per comunitats forals + resta españa (potser per provincies?),
# detallant; nom/raó social, NIF, direcció suministre, import facturat (detallant si porta IVA o no) periode de consum.
# Aquestes dades s'han de presentar agregades a nivell de exercici fiscal complet dels anys 2017, 2018, 2019 i 2020
# CUPS;nombre;nif;direccion_subministro;territorio;importe_facturado; iva; periodo_inicio; periodo_fin
# ES0000000000000000000; Nom client; 12345678A; Carrer numero; True; 1000; True; 2020-01-15; 2021-01-15


FOLDER = '1CQvIZCZ3Urqr01ZLKdtcUioh2pjMa-jZ'

class MoveReport:
    def __init__(self, cursor):
        self.cursor = cursor
        pass

    def move_by_lines(self, start_date, end_date):
        sql = '''
            SELECT  gcp.name, pagador.name, pagador.vat as nif,
                gcp.direccio AS direccion_subministro,
            CASE rcs.code
                WHEN '31' THEN 'Navarra'
                WHEN '01' THEN 'Alava'
                WHEN '20' THEN 'Guipuzkoa'
                WHEN '48' THEN 'Bizkaya'
                ELSE 'resto impuesto'
            END AS territorio,
            round(
                (sum(
                case
                    WHEN tax.name = 'SIN IMPUESTO' THEN
                    CASE
                        when factura.type = 'out_refund' then
                            tax.base_amount * -1
                        else
                            tax.base_amount
                        end
                    ELSE tax.base_amount
                END)
                +
                sum(
                        CASE
                        when factura.type = 'out_refund' then
                            tax.tax_amount * -1
                        else
                            tax.tax_amount
                        end
                )), 2
            ) as importe_facturado,
            'si' as iva_incluido,
            min(gff.data_inici) AS periodo_inicio,
            max(gff.data_final) AS perido_fin

            FROM account_invoice factura
            INNER JOIN account_journal journal  ON journal.id = factura.journal_id
            INNER JOIN account_invoice_tax tax on factura.id = tax.invoice_id
            inner join giscedata_polissa gp on gp.pagador = factura.partner_id
            inner JOIN giscedata_cups_ps gcp ON gcp.id = gp.cups
            inner join res_partner pagador on pagador.id = gp.pagador
            inner JOIN giscedata_facturacio_factura gff ON gff.invoice_id = factura.id
            LEFT JOIN res_municipi rm ON rm.id = gcp.id_municipi
            LEFT JOIN res_country_state rcs ON rm.state = rcs.id
            where
                gff.polissa_id  = gp.id and
                factura.date_invoice  between '{0}'  and '{1}'
                and journal.id in (1,5,6,7,8)
                and journal.include_to_iva_book
                and tax.name ilike 'IVA%%'
                and factura.state in ('open','paid')
            group by gcp.name, pagador.name,pagador.vat, gcp.direccio, rcs.code

            '''.format(start_date, end_date)

        self.cursor.execute(sql)

        file_name = '/tmp/listado_contadores_' + str(start_date[:4]) + '.csv'
        self.build_report(self.cursor.fetchall(), file_name)
        driveUtils.upload(file_name, FOLDER)
        print "From ", start_date, " to ", end_date, " exported."


    def build_report(self, records, filename):
        with codecs.open(filename,'wb','utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"')
            writer.writerow(['cups','nombre','nif','direccion_subministro','territorio','importe_facturado', 'iva_incluido', 'periodo_inicio', 'periodo_fin'])
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
    m.move_by_lines(start_date, end_date)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='descarregar_assentaments_comptables.py', description='Descarrega assentaments comptables al Drive.')
    parser.add_argument('-s','--start_date', help='Data inicial des de la qual es volen assentaments.', required=True)
    parser.add_argument('-e','--end_date', help='Data final fins la qual es volen assentaments.', required=True)
    args = parser.parse_args(sys.argv[1:])
    main(args)

# vim: et ts=4 sw=4
