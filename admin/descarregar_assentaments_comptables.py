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

## SYNTAX
# descarregar_assentaments_comptables.py

class MoveReport:
    def __init__(self, cursor):
        self.cursor = cursor
        pass

    def move_by_month(self, start_date, end_date):
        sql = '''
            SELECT acm.name AS numero, 
                acm.date AS data,
                acc.name AS compte,
                acc.code AS codi,
                acm_line.debit AS deure,
                acm_line.credit AS haver

            FROM account_move AS acm
                LEFT JOIN account_move_line AS acm_line ON acm.id=acm_line.move_id
                LEFT JOIN account_account AS acc ON acc.id = acm_line.account_id
            WHERE acm.date >= '{0}' 
                AND acm.date <= '{1}'
            ORDER BY acm.date, 
                acm.name
            '''.format(start_date, end_date)

        self.cursor.execute(sql, {'start_date': start_date,
                                  'end_date': end_date})

        file_name = '/tmp/assent_interv_' + start_date + '.csv'
        self.build_report(self.cursor.fetchall(), file_name)
        driveUtils.upload(file_name)

    def build_report(self, records, filename):

        with codecs.open(filename,'wb','utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['numero', 'data', 'compte', 'codi', 'deure','haver'])
 
            for record in records:
                number = record[0]
                date = record[1]
                account = record[2]
                code = record[3]
                debe = record[4]
                haber = record[5]
                writer.writerow([number, date, account, code, debe, haber])


def main(year):
    reload(sys)  
    sys.setdefaultencoding('utf8')

    try:
        dbconn=psycopg2.connect(**configdb.psycopg)
    except Exception, ex:
        print "Unable to connect to database " + configdb['DB_NAME']
        raise ex

    m = MoveReport(dbconn.cursor())


    start_date = datetime.strptime(year, '%Y')
    end_date = start_date

    for i in range(12):
        start_date = end_date
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)

        #m.move_by_month(start_date, end_date)

        end_date = end_date + relativedelta(days=1)

main(sys.argv[1])

# vim: et ts=4 sw=4
