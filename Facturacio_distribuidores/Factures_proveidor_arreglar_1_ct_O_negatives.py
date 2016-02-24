from ooop import OOOP
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import configdb
 
O = OOOP(**configdb.ooop)

#Objectes
fact_obj = O.GiscedataFacturacioFactura

def getFact_1ct(db):
    sql_query = """
            select factura.id as factura_id,
           	inv.date_invoice,
           	inv.type,
           	factura.tipo_rectificadora,
           	inv.check_total,
           	inv.amount_total,
           	(inv.check_total - inv.amount_total),
           	inv.origin
            
            from giscedata_facturacio_factura as factura
            left join account_invoice as inv on inv.id = factura.invoice_id
            
            where   inv.type = 'in_invoice' and
           	inv.state = 'draft' and
           	abs(inv.check_total - inv.amount_total) < 0.021
           	and (inv.check_total - inv.amount_total) != 0
            
            order by inv.date_invoice

        """

    try:
        db.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        raise ex

    extra_data = []
    for record in db.fetchall():
        extra_data.append (record['factura_id'])

    return (extra_data)

def getFact_neg(db):
    sql_query = """
            select factura.id as factura_id,
           	inv.date_invoice,
           	inv.type,
           	factura.tipo_rectificadora,
           	inv.check_total,
           	inv.amount_total,
           	(inv.check_total - inv.amount_total),
           	inv.origin
            
            from giscedata_facturacio_factura as factura
            left join account_invoice as inv on inv.id = factura.invoice_id
            
            where   inv.type = 'in_invoice' and
           	inv.state = 'draft' and
           	abs(inv.check_total) = abs(inv.amount_total)
           	and (inv.check_total != inv.amount_total)
         """

    try:
        db.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        raise ex

    extra_data = []
    for record in db.fetchall():
        extra_data.append (record['factura_id'])

    return (extra_data)

try:
    pg_con = " host=" + configdb.pg['DB_HOSTNAME'] + \
             " port=" + str(configdb.pg['DB_PORT']) + \
             " dbname=" + configdb.pg['DB_NAME'] + \
             " user=" + configdb.pg['DB_USER'] + \
             " password=" + configdb.pg['DB_PASSWORD']
    dbconn=psycopg2.connect(pg_con)
except Exception, ex:
    print "Unable to connect to database " + configdb.pg['DB_NAME']
    raise ex

dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
factura_1ct_ids = getFact_1ct(dbcur)
factura_neg_ids = getFact_neg(dbcur)
factura_ids = sorted(list(set(factura_1ct_ids + factura_neg_ids)))


factura_reads = fact_obj.read(factura_ids,['check_total','amount_total'])


n = 0
for factura_read in factura_reads:
    fact_obj.write(factura_read['id'],{'check_total':factura_read['amount_total']})
    n+=1
    print "%d/%d" % (n,len(factura_reads))

