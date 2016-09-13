#! /usr/bin/env python2
import psycopg2
import psycopg2.extras
import csv
from ooop import OOOP


import sys
from datetime import datetime,date,timedelta

import configdb


def dump(title,factures):
     print "==== %s ====" % title
     for factura in factures:
         if ('polissa' in factura) and ('factura' in factura):
             print factura['polissa'], factura['factura']


def db_query(db,sql):
    try:
        db.execute(sql)
    except Exception ,ex:
        print 'Failed executing query'
        print sql
        raise ex

    return db.fetchall()


def get_factures_0days(db,lots):
    sql_query = '''
        SELECT polissa.name AS polissa,invoice.number AS factura,invoice.id AS invoice_id, factura.id AS factura_id,factura.data_inici,factura.data_final,factura.energia_kwh,invoice.state
        FROM giscedata_facturacio_factura AS factura
        LEFT JOIN giscedata_facturacio_factura_linia AS factura_linia ON factura.id = factura_linia.factura_id
        LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
        LEFT JOIN giscedata_facturacio_contracte_lot_factura AS factura_lot ON factura_lot.factura_id = factura.id
        LEFT JOIN account_invoice AS invoice ON invoice.id = factura.invoice_id
        LEFT JOIN giscedata_facturacio_contracte_lot AS contracte_lot ON contracte_lot.id = factura_lot.contracte_lot_id
        LEFT JOIN giscedata_facturacio_lot AS lot ON lot.id = contracte_lot.lot_id
        WHERE lot.name IN (\'%s\')
        AND (invoice.type IN ('out_invoice','out_refund'))
        AND invoice.state = 'draft'
        AND (factura.data_final-factura.data_inici) = 0
        GROUP BY polissa.name,factura.id,invoice.id,invoice.number,invoice.state
    ''' %  '\',\''.join(map(str,lots))
    return db_query(db,sql_query)

def get_factures_0energyLines(db,lots):
    sql_query = '''
        SELECT polissa.name AS polissa,invoice.number AS factura,invoice.id AS invoice_id, factura.id AS factura_id,factura.data_inici,factura.data_final,factura.energia_kwh,invoice.state
        FROM giscedata_facturacio_factura AS factura
        LEFT JOIN giscedata_facturacio_lectures_energia AS linia_energia ON factura.id = linia_energia.factura_id
        LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
        LEFT JOIN giscedata_facturacio_contracte_lot_factura AS factura_lot ON factura_lot.factura_id = factura.id
        LEFT JOIN account_invoice AS invoice ON invoice.id = factura.invoice_id
        LEFT JOIN giscedata_facturacio_contracte_lot AS contracte_lot ON contracte_lot.id = factura_lot.contracte_lot_id
        LEFT JOIN giscedata_facturacio_lot AS lot ON lot.id = contracte_lot.lot_id
        WHERE lot.name IN (\'%s\')
        AND (invoice.type IN ('out_invoice','out_refund'))
        AND invoice.state = 'draft'
        GROUP BY polissa.name,factura.id,invoice.id,invoice.number,invoice.state
        HAVING SUM(CASE WHEN linia_energia.tipus='activa' THEN 1 ELSE 0 END) = 0
    ''' %  '\',\''.join(map(str,lots))
    return db_query(db,sql_query)



def get_factures_0days_today(db,lots):
    today = datetime.strftime(datetime.today(),'%Y-%m-%d')
    sql_query = '''
        SELECT polissa.name AS polissa,invoice.number AS factura,invoice.id AS invoice_id, factura.id AS factura_id,factura.data_inici,factura.data_final,factura.energia_kwh,invoice.state
        FROM giscedata_facturacio_factura AS factura
        LEFT JOIN giscedata_facturacio_factura_linia AS factura_linia ON factura.id = factura_linia.factura_id
        LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
        LEFT JOIN account_invoice AS invoice ON invoice.id = factura.invoice_id
        WHERE (invoice.type IN ('out_invoice','out_refund'))
        AND invoice.state = 'draft'
        AND invoice.date_invoice = '{today}'
        AND (factura.data_final-factura.data_inici) = 0
        GROUP BY polissa.name,factura.id,invoice.id,invoice.number,invoice.state
    '''.format(**locals())
    return db_query(db,sql_query)

def get_factures_0energyLines_today(db,lots):
    today = datetime.strftime(datetime.today(),'%Y-%m-%d')
    sql_query = '''
        SELECT polissa.name AS polissa,invoice.number AS factura,invoice.id AS invoice_id, factura.id AS factura_id,factura.data_inici,factura.data_final,factura.energia_kwh,invoice.state
        FROM giscedata_facturacio_factura AS factura
        LEFT JOIN giscedata_facturacio_lectures_energia AS linia_energia ON factura.id = linia_energia.factura_id
        LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
        LEFT JOIN account_invoice AS invoice ON invoice.id = factura.invoice_id
        WHERE (invoice.type IN ('out_invoice','out_refund'))
        AND invoice.state = 'draft'
        AND invoice.date_invoice = '{today}'
        GROUP BY polissa.name,factura.id,invoice.id,invoice.number,invoice.state
        HAVING SUM(CASE WHEN linia_energia.tipus='activa' THEN 1 ELSE 0 END) = 0
    '''.format(**locals())
    return db_query(db,sql_query)

def get_factures_rel(O,factura):
    factura_ids = O.GiscedataFacturacioFactura.search([
        ('polissa_id','=',factura['polissa']),
        ('invoice_id.state','=','draft'),
        ('id','!=',factura['factura_id']),
        ('data_inici','=',datetime.strftime((factura['data_final'] + timedelta(1)),'%Y-%m-%d'))
    ])

    fields_to_read = ['id','name','data_inici','data_final','energia_kwh','state']
    factures = O.GiscedataFacturacioFactura.read(factura_ids,fields_to_read)

    result = []
    for factura_ in factures:
        result.append(
            {
                'polissa':factura['polissa'],
                'factura':factura_['name'],
                'factura_id':factura_['id'],
                'invoice_id':factura_['invoice_id'],
                'data_inici':factura_['data_inici'],
                'data_final':factura_['data_final'],
                'energia_kwh':factura_['energia_kwh'],
                'state':factura_['state']
            }

        )
    return result

def eliminar_factura(O, factura):
    try:
        O.GiscedataFacturacioFactura.unlink([factura['factura_id']])
    except Exception, ex:
        print ex

dbcur = None
try:
    pg_con = " host=" + configdb.pg['DB_HOSTNAME'] + \
             " port=" + str(configdb.pg['DB_PORT']) + \
             " dbname=" + configdb.pg['DB_NAME'] + \
             " user=" + configdb.pg['DB_USER'] + \
             " password=" + configdb.pg['DB_PASSWORD']
    dbconn=psycopg2.connect(pg_con)
    dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
except Exception, ex:
    print "Unable to connect to database " + configdb['DB_NAME']
    raise ex

O = None
try:
    O = OOOP(dbname=configdb.ooop['dbname'], user=configdb.ooop['user'], pwd=configdb.ooop['pwd'], port=configdb.ooop['port'], uri=configdb.ooop['uri'])
except Exception, ex:
    raise ex

lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
lot_name = O.GiscedataFacturacioLot.read(lot_id,['name'])['name']
lots = [lot_name]

try:
    factures = get_factures_0energyLines(dbcur, lots)
    for factura in factures:
        if not factura['energia_kwh']:
            eliminar_factura(O, factura)
    dump('Energy 0 lines', factures)

    factures = get_factures_0days(dbcur, lots)
    for factura in factures:
        eliminar_factura(O, factura)
    dump('Energy 0 days', factures)
except Exception, ex:
    print "Error llegint les factures dels lots"
    raise ex
