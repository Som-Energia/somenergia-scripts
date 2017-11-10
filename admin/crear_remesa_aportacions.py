#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from erppeek import Client
import configdb
import unicodedata
import psycopg2
import psycopg2.extras
import datetime
import decimal

'''
    Busca entre els moviments comptables els que són del tipus "títols participatius" (1714X) entre 
    el 01/01/2012 (data títols 5 anys) i la data entrada per paràmetre amb format DD-MM-AAAA. El segon
    paràmetre és l'id de la remesa que s'ha creat prèviament

    python admin/crear_remesa_aportacions.py 2012-10-09 2313
'''
def accountBalanceTitols(db):
    #return [{'debe': decimal.Decimal('60000.00'), 'balance': decimal.Decimal('-10000.00'), 'haber': decimal.Decimal('70000.00'), 'account_id': 6280, 'min': datetime.date(2012, 10, 8)}]
    sql_query = """
        SELECT min(date), account_id, sum(debit) as debe, sum(credit) as haber,  ( sum(debit) -  sum(credit) ) as balance
        FROM public.account_move_line
        WHERE account_id IN  (
            SELECT id
            FROM public.account_account
            WHERE code ilike '17140%'
            )
            AND state = 'valid'
        GROUP BY account_id
        HAVING ( sum(debit) -  sum(credit) ) < 0 
        AND min(date) > '2012-09-30'
        ORDER BY account_id;
        """

    try:
        db.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        error=True
        raise ex

    extra_data = []
    for record in db.fetchall():
        extra_data.append (record)

    return (extra_data)


def numSociToString(nsoci):
    nsoci_str = str(nsoci)
    nzeros = 6 - len(nsoci_str)
    for n in range(0,nzeros):
        nsoci_str = '0' + nsoci_str
    return 'S' + nsoci_str
    

def netejar_remesa(data_max, balance, order_id):
    reload(sys)
    sys.setdefaultencoding('utf8')

    O = Client(**configdb.erppeek)

    print 'Retorn de títols de 5 anys fins a ', data_max

    po_obj = O.PaymentOrder
    pl_obj = O.PaymentLine
    rp_obj = O.ResPartner
    aa_obj = O.AccountAccount
    ss_obj = O.SomenergiaSoci

    po_read = po_obj.read(order_id)

    i = 0
    for record in balance:
        data_reg = record['min']
        data_param = datetime.datetime.strptime(data_max, '%Y-%m-%d').date()
        if data_reg < data_param:
            quantitat = record['balance']
            account_id = record['account_id']
            account_obj = aa_obj.read(account_id, [])
            account_code = account_obj['code']
            #obtenim nsoci a traves de compte comptable
            nsoci = int(account_code[4:])
            nsoci_str = numSociToString(nsoci)
            #"anem a buscar el soci: ", nsoci_str
            partner_id = rp_obj.search([('ref','=',nsoci_str)])            
            #"anem a llegir partner: ", partner_id
            partner_obj = rp_obj.read(partner_id[0])

            bank_inversions = '' 
            if partner_obj['bank_inversions']:
                bank_inversions = partner_obj['bank_inversions'][0]
            pl_obj.create({
                'order_id': str(order_id), 
                'partner_id': partner_id[0], 
                'amount_currency': str(quantitat*(-1)), 
                'communication': 'RETORN TITOLS',
                'account_id': account_id,
                'bank_id': bank_inversions,
            })
        i = i + 1
    print "Afegides ", i, " linies a la remesa"


try:
    pg_con = " host=" + configdb.pg['DB_HOSTNAME'] + \
             " port=" + str(configdb.pg['DB_PORT']) + \
             " dbname=" + configdb.pg['DB_NAME'] + \
             " user=" + configdb.pg['DB_USER'] + \
             " password=" + configdb.pg['DB_PASSWORD']
    dbconn=psycopg2.connect(pg_con)
except Exception, ex:
    print "Unable to connect to database " + configdb.pg['DB_NAME']
    error=True
    raise ex

try:
    sys.argv[1]
    sys.argv[2]
except Exception, ex:
    print "Falten Parametres"
    raise ex

dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
balance = accountBalanceTitols(dbcur)
netejar_remesa(sys.argv[1], balance, sys.argv[2])

# vim: et ts=4 sw=4
