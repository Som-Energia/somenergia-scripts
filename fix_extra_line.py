from ooop import OOOP
from datetime import datetime,timedelta
import sys

from ooop import OOOP
import psycopg2
import psycopg2.extras
import sys
from datetime import datetime
from collections import defaultdict
from tabulate import tabulate
import csv

import dbconfig

# CONSTANTS
# Quantity threshold
QUANTITY_MAX = 100


O = OOOP(**configdb.ooop)

def getOverQuantityExtra(db,quantity):

    sql_query = """
        SELECT extra.id AS id,
            polissa.id AS polissa_id,
            polissa.name AS polissa_name,
            extra.price_unit,
            extra.quantity,
            template.description
        FROM giscedata_facturacio_extra AS extra
        LEFT JOIN giscedata_polissa AS polissa ON extra.polissa_id=polissa.id
        LEFT JOIN product_product AS product ON extra.product_id=product.id
        LEFT JOIN product_template AS template ON product.product_tmpl_id=template.id
        WHERE extra.price_unit>'1'
        AND extra.quantity>'%d'
    """ % (quantity)

    try:
        db.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        raise ex

    extra_data = []
    for record in db.fetchall():
        extra_data.append (
            {'id': record['id'],
             'polissa_id': record['polissa_id'],
             'polissa_name': record['polissa_name'],
             'price_unit': record['price_unit'],
             'quantity': record['quantity'],
             'description': record['description'],
             }
        )

    return (extra_data)


def updateQuantity(extra_id,quantity):
    vals_extra = {'quantity':quantity}
    print 'Actualitzacio: %d %0.2f' % (extra_id,quantity)
    O.GiscedataFacturacioExtra.write([extra_id],vals_extra);


try:
    dbconn=psycopg2.connect(**configdb.psycopg)
except Exception, ex:
    print "Unable to connect to database " + configdb.psycopg['database']
    raise ex

dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
(extra_data)= getOverQuantityExtra(dbcur,QUANTITY_MAX)

table = []
headers_ = ['id','polissa_id','polissa_name','price_unit','quantity','new_quantity','description']
for extra in extra_data:
    new_quantity = float(extra['quantity'])/1000
    updateQuantity(extra['id'],new_quantity)
    table.append([
        extra['id'],
        extra['polissa_id'],
        extra['polissa_name'],
        extra['price_unit'],
        extra['quantity'],
        new_quantity,
        unicode(extra['description'],"utf-8")
    ])
print tabulate(table,headers=headers_)
