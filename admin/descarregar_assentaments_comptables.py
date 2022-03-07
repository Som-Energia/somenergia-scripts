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
locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
import argparse

## SYNTAX
# python admin/descarregar_assentaments_comptables.py --start_date 2018-01-10 --end_date 2018-01-20

MAX_MOVES_LINES = 700000 #Max linies assentament del programa dels interventors
FOLDER = '18f1DXG8V5QmCBKivozHldvcob6opldN1'

class MoveReport:
    def __init__(self, cursor):
        self.cursor = cursor
        pass

    def get_account_ids(self, account_code):
        if not account_code:
            return []
        account_sql = '''
            SELECT id
                FROM account_account AS acc
            WHERE code like '{}'
        '''.format(account_code)

        self.cursor.execute(account_sql, {'account': account_code})
        return self.cursor.fetchone()

    def count_moves_of_year(self, start_date, end_date, account_ids):
        sql = '''
                SELECT count(*)
                    FROM account_move_line AS acm
            WHERE acm.date >= '{0}'
                AND acm.date <= '{1}'
            '''.format(start_date, end_date)

        if account_ids:
            sql += ''' AND acm.account_id in ({}) '''.format(','.join(str(_id) for _id in account_ids))

        self.cursor.execute(sql, {'start_date': start_date,
                                  'end_date': end_date})
        result = self.cursor.fetchone()

        return int(result[0])

    def move_by_lines(self, start_date, end_date, start_line, end_line, account_ids):
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
            '''.format(start_date, end_date)

        if account_ids:
            sql += ''' AND acm_line.account_id in ({}) '''.format(','.join(str(_id) for _id in account_ids))

        sql +=  '''
            ORDER BY acm.date,
                acm.name
                OFFSET {0} LIMIT {1}
            '''.format(start_line, MAX_MOVES_LINES)

        print sql
        self.cursor.execute(sql, {'start_date': start_date,
                                  'end_date': end_date,
                                    'start_line': start_line,
                                    'MAX_MOVES_LINES': MAX_MOVES_LINES,})

        file_name = '/tmp/assent_interv_' + str(start_date) + "_" +  str(start_line) + '.csv'
        self.build_report(self.cursor.fetchall(), file_name)
        driveUtils.upload(file_name, FOLDER)
        print "From ", start_line, " to ", end_line, " exported."

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

        file_name = '/tmp/assent_interv_' + start_date.strftime("%Y-%m-%d") + '.csv'
        self.build_report(self.cursor.fetchall(), file_name)
        driveUtils.upload(file_name, FOLDER)
        print "From ", start_date, " to ", end_date, " exported."

    def build_report(self, records, filename):

        with codecs.open(filename,'wb','utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["número", 'data', 'compte', 'codi', 'deure','haver'])
 
            for record in records:
                number = record[0]
                date = record[1]
                account = record[2]
                code = record[3]
                try:
                    debe = locale.format("%.2f", record[4])
                except Exception, ex:
                    debe = 0
                try:
                    haber = locale.format("%.2f", record[5])
                except  Exception, ex:
                    haber = 0
                writer.writerow([number, date, account, code, debe, haber])


def main(args):
    reload(sys)
    sys.setdefaultencoding('utf8')

    start_date =  args.start_date
    end_date = args.end_date
    account = args.account

    try:
        dbconn=psycopg2.connect(**configdb.psycopg)
        dbconn.set_client_encoding('UTF8')
    except Exception, ex:
        print "Unable to connect to database " + configdb['DB_NAME']
        raise ex

    m = MoveReport(dbconn.cursor())

    account_ids = []

    account_ids = m.get_account_ids(args.account)
    lines = m.count_moves_of_year(start_date, end_date, account_ids)
    start_line = 0
    end_line = 0

    while start_line < lines:
        end_line = start_line + MAX_MOVES_LINES
        m.move_by_lines(start_date, end_date, start_line, end_line, account_ids)
        start_line = end_line + 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='descarregar_assentaments_comptables.py', description='Descarrega assentaments comptables al Drive.')
    parser.add_argument('-s','--start_date', help='Data inicial des de la qual es volen assentaments.', required=True)
    parser.add_argument('-e','--end_date', help='Data final fins la qual es volen assentaments.', required=True)
    parser.add_argument('-a','--account', help='Compte comptable del qual es volen els assentaments')
    args = parser.parse_args(sys.argv[1:])
    main(args)
# vim: et ts=4 sw=4
