#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime,timedelta
import psycopg2
import psycopg2.extras
import csv
import sys


O = OOOP(**configdb.ooop)

def getErrorCanviComptador(db):
    sql_query = """
        SELECT comptador.id AS comptador_id,
	       polissa.id AS polissa_id,
	       polissa.data_ultima_lectura AS data_ultima_lectura,
	       lectura.name AS data_lectura,
	       (polissa.data_ultima_lectura -lectura.name) AS dies_dif_lectures

        FROM giscedata_lectures_comptador AS comptador
        LEFT JOIN giscedata_lectures_lectura AS lectura ON lectura.comptador = comptador.id
        LEFT JOIN giscedata_polissa AS polissa ON polissa.id = comptador.polissa
    

        WHERE comptador.data_baixa < lectura.name
	       AND polissa.active
	       AND (polissa.data_ultima_lectura -lectura.name)<36

        GROUP BY comptador.name, polissa.name, polissa.data_ultima_lectura, lectura.name

        ORDER BY polissa.data_ultima_lectura - lectura.name
        """ 
    try:
        db.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        raise ex

    extra_data = []
    for record in db.fetchall():
        extra_data.append (
            {'comptador_id': record['comptador_id'],
             'polissa_id': record['polissa_id'],
             'data_ultima_lectura': record['data_ultima_lectura'],
             'data_lectura': record['data_lectura'],
             'dies_dif_lectures': record['dies_dif_lectures']
             }
        )

    return (extra_data)
try:
    dbconn=psycopg2.connect(**configdb.psycopg)
except Exception, ex:
    print "Unable to connect to database " + configdb['database']
    raise ex

dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
(extra_data)= getErrorCanviComptador(dbcur)

print extra_data
