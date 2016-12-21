#! /usr/bin/env python2
import psycopg2
import psycopg2.extras
import csv
from ooop import OOOP


import sys

import configdb


def dump(title,factures):
     print "==== %s ====" % title
     for factura in factures:
         if ('polissa' in factura) and ('factura' in factura):
             print factura['polissa'], factura['factura_id']


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
        SELECT polissa.name AS polissa, polissa.id AS polissa_id, invoice.number AS factura,invoice.id AS invoice_id, factura.id AS factura_id,factura.data_inici,factura.data_final,factura.energia_kwh,invoice.state
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
        GROUP BY polissa.name,factura.id,invoice.id,invoice.number,invoice.state, polissa.id
        HAVING SUM(CASE WHEN linia_energia.tipus='activa' THEN 1 ELSE 0 END) = 0
    ''' %  '\',\''.join(map(str,lots))
    return db_query(db,sql_query)



def eliminar_factures(O, polissa_id):
    try:
        factura_ids = O.GiscedataFacturacioFactura.search([('polissa_id','=',polissa_id),
                                                            ('state','=','draft'),
                                                            ('type','=','out_invoice')])
        O.GiscedataFacturacioFactura.unlink(factura_ids,{})
    except Exception, ex:
        print ex

def sumar_dies_mod_contractual(O,mod_id,active,dies):
    from datetime import datetime, timedelta
    mod_obj = O.GiscedataPolissaModcontractual
    try:
        data_tipus = 'data_final'    
        if active:
            data_tipus = 'data_inici'
        data = mod_obj.read([mod_id],[data_tipus])[0][data_tipus]
        data_result_dt = datetime.strptime(data,'%Y-%m-%d') + timedelta(dies)
        data_result = datetime.strftime(data_result_dt,'%Y-%m-%d')
        mod_obj.write([mod_id],{data_tipus:data_result})
    except:
        print "problemes en sumar el dia"

def alinear_mod_contractuals(O,polissa_id):
    mod_obj = O.GiscedataPolissaModcontractual
    try:    
        mod_activa_id = mod_obj.search([('polissa_id','=',polissa_id)])[0]
        mod_inactiva_id = mod_obj.search([('polissa_id','=',polissa_id),
                                            ('active','=',False)])[0]
            
        sumar_dies_mod_contractual(O,mod_inactiva_id,False,1)    
        sumar_dies_mod_contractual(O,mod_activa_id,True,1) 
    except:
        print "problemes en alinear_mod_contractual"
    
def refacturar(polissa_id):
    print "Per ara no refacturem"
 


dbcur = None
try:
    pg_con = " host=" + configdb.pg['DB_HOSTNAME'] + \
             " port=" + str(configdb.pg['DB_PORT']) + \
             " dbname=" + configdb.pg['DB_NAME'] + \
             " user=" + configdb.pg['DB_USER'] + \
             " password=" + configdb.pg['DB_PASSWORD']
    #dbconn=psycopg2.connect(pg_con)
    dbconn=psycopg2.connect(**configdb.psycopg)
    dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
except Exception, ex:
    print "Unable to connect to database " + configdb.pg['DB_NAME']
    raise ex

O = None
try:
    O = OOOP(dbname=configdb.ooop['dbname'], user=configdb.ooop['user'], pwd=configdb.ooop['pwd'], port=configdb.ooop['port'], uri=configdb.ooop['uri'])
except Exception, ex:
    raise ex

lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
lot_name = O.GiscedataFacturacioLot.read([lot_id],['name'])[0]['name']
lots = [lot_name]

try:
    factures = get_factures_0energyLines(dbcur, lots)
    for factura in factures:
        if not factura['energia_kwh']:
            print int(factura['polissa_id'])
            eliminar_factures(O, int(factura['polissa_id']))
            alinear_mod_contractuals(O,int(factura['polissa_id']))
            refacturar(factura['polissa_id'])
    dump('Energy 0 lines', factures)

    factures = get_factures_0days(dbcur, lots)
    for factura in factures:
        print "0 days. No fem re!"        
        #eliminar_factures(O, int(factura['polissa_id']))
    dump('Energy 0 days', factures)
except Exception, ex:
    print "Error llegint les factures dels lots"
    raise ex
