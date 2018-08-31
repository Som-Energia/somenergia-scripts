# -*- coding: utf-8 -*-

from ooop import OOOP
import psycopg2
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

#ENVIAMENT MENSUAL
#Enviament/execució petició de lectures estimades
#Executar script peticio_lectures_estimades.py
#Recordar que s'ha de canviar la data de l'interval i afegir que tingui en compte que si hi ha F1 no és
#necessari pq en aquest cas ja tindrem lectures reals
# Mirar la implementació de l'omplir correu per a l'accés als F1

import configdb

polisses_process_prev = []


# Default
TODAY_ = datetime.today()
TODAY = TODAY_.strftime('%Y/%m/%d')

DEFAULT_MIN_DATE_ = TODAY_+relativedelta(months=-5)
DEFAULT_MIN_DATE = DEFAULT_MIN_DATE_.strftime('%Y/%m/%d')
DEFAULT_SENT_DATE_ = TODAY_+relativedelta(months=-2)
DEFAULT_SENT_DATE = DEFAULT_SENT_DATE_.strftime('%Y/%m/%d')

# Constants
ORIGEN_ID = [7,9] #Identificacio dels origens de les lectures estimades i sense lectura
DISTR_AUTO_ID = [2273,2280,2437,2316] # Identificador distribuidores tractament automàtic ENDESA,Iberdrola, EON, Union Fenosa



def getPolissesExcesEstimades(db,min_data,in_,distrs):

    not_in = ''
    if not in_:
        not_in = 'NOT'

    sql_query = """
                SELECT polissa.id
                FROM giscedata_polissa AS polissa
                LEFT JOIN res_partner AS rp ON rp.id = polissa.distribuidora
                LEFT JOIN giscedata_polissa_category_rel AS category_rel ON polissa.id=category_rel.polissa_id
                LEFT JOIN giscedata_polissa_category AS category ON category.id = category_rel.category_id
                LEFT JOIN giscedata_polissa_category AS category_ ON category_.id = category.parent_id
                WHERE polissa.id NOT IN
                (  SELECT comptador.polissa
                    FROM giscedata_lectures_lectura_pool AS lectura
                    LEFT JOIN giscedata_lectures_comptador AS comptador on comptador.id = lectura.comptador
                    WHERE lectura.name > '%s'
                    AND lectura.origen_id NOT IN (%s)
                    GROUP BY lectura.comptador, comptador.polissa
                    ORDER BY comptador.polissa
                )
                AND (category_.name IS NULL OR category_.name != 'En curs')
                AND polissa.active
                AND polissa.state ='activa'
                AND polissa.data_alta < '%s'
                AND polissa.distribuidora %s IN (%s)""" % \
                (min_data,
                 ','.join(map(str,ORIGEN_ID)),
                 min_data,
                 not_in,
                 ','.join(map(str,distrs)))

    try:
        db.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        print sql_query
        raise ex

    return [record[0] for record in db.fetchall()]



#if __name__ == "__main__":

min_date = DEFAULT_MIN_DATE
sent_date = DEFAULT_SENT_DATE
args = sys.argv[1:]
n_msgs = int(args[0])

try:
    dbconn=psycopg2.connect(**configdb.psycopg)
except Exception, ex:
    print "Unable to connect to database " + str(configdb.psycopg)
    raise ex

dbcur = dbconn.cursor()

polisses_process_auto = []
try:
    polisses_process_auto = getPolissesExcesEstimades(dbcur,min_date,True,DISTR_AUTO_ID)
except Exception, ex:
    print "Error llegint polisses amb lectures estimades"
    raise ex

polisses_process_manual = []
try:
    polisses_process_manual = getPolissesExcesEstimades(dbcur,min_date,False,DISTR_AUTO_ID)
except Exception, ex:
    print "Error llegint polisses amb lectures estimades"
    raise ex


O = OOOP(**configdb.ooop)

avui = datetime.today()
avui_ = avui.strftime('%Y/%m/%d')

from_id = O.PoweremailCore_accounts.search([('email_id','=','factura@somenergia.coop')])
template_id = O.PoweremailTemplates.search([('name','=',u'Petici\xf3 lectura comptador OV')])
#enviats_ids = O.PoweremailMailbox.search([('pem_subject','ilike','Som energia: Lectura de consum (contracte'),('date_mail','>',min_date)])
enviats_ids = O.PoweremailMailbox.search([('pem_subject','ilike',u'Petici\xf3 lectura comptador'),('date_mail','>',sent_date), ('folder','=','sent')])
enviats = O.PoweremailMailbox.read(enviats_ids,['reference','date_mail'])
polisses_enviats_auto = [int(polissa_ref['reference'].split(',')[1]) for polissa_ref in enviats]

polisses_enviats_auto = O.GiscedataPolissa.search([('id','in',polisses_enviats_auto)])

polisses_process_auto = list(set(polisses_process_auto)-set(polisses_process_prev))
polisses_process_auto = list(set(polisses_process_auto)-set(polisses_enviats_auto))


enviats = []
noenviats = []
tarifa30A = []

for polissa_id in polisses_process_auto[:n_msgs]:
    polissa = O.GiscedataPolissa.read(polissa_id,['name','tarifa','observacions'])

    if polissa['tarifa'][1] == '3.0A':
        tarifa30A.append(polissa_id)
        continue

    #enviar mail de petició de lectura
    ctx = {'active_ids': [polissa_id],
           'active_id': polissa_id,
           'template_id': template_id[0],
           'src_model': 'giscedata.polissa',
           'src_rec_ids': [polissa_id],
           'from': from_id[0]}

    params = {'state': 'single',
              'priority':0,
              'from': ctx['from']}

    try:
        wz_id = O.PoweremailSendWizard.create(params, ctx)
        O.PoweremailSendWizard.send_mail([wz_id], ctx)
        enviats.append(polissa_id)
    except Exception , ex:
        noenviats.append(polissa_id)
        print ex
        continue

    print "Mail enviat a la polissa %s " % (polissa['name'])
    if polissa['observacions']:
        obs = "%s (automaticament,script) \nMail de peticio de lectura: 5 mesos sense recepcio lectura real\n\n" % avui_ + polissa['observacions']
    else:
        obs = "%s (automaticament,script) \nMail de peticio de lectura: 5 mesos sense recepcio lectura real\n\n" % avui_
    O.GiscedataPolissa.write(polissa_id,{'observacions':obs})
