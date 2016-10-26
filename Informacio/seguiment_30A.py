from erppeek import Client
from datetime import datetime,timedelta
import configdb
import psycopg2
import psycopg2.extras
import argparse

O = Client(**configdb.erppeek)

pol_obj = O.GiscedataPolissa
sw_obj = O.GiscedataSwitching

parser = argparse.ArgumentParser(description='Seguiment de casos de contractes amb 3.0A')
parser.add_argument('-d','--date',required=False)
args = vars(parser.parse_args()) 
data_inici = args['date']

tarifa = '3.0A'
data = '2016-03-15'
if not(data_inici):
    data_inici = datetime.today().strftime('%Y-%m-%d')

def contractesNous(tarifa, data_inici):
    tots = []    
    sense_not = []
    mails = ['tarifa3.0@somenergia.coop','ccvv@somenergia.coop']
    data_fi = datetime.strftime(datetime.today(),'%Y-%m-%d')
    pol_ids = pol_obj.search([('tarifa.name','=',tarifa),
                       ('data_firma_contracte','>=',data_inici),
                       ('data_firma_contracte','<',data_fi)])
    sol_pol = len(pol_ids)
    pol_reads = pol_obj.read(pol_ids,
                        ['notificacio_email','cups'])
    for pol_read in pol_reads:
        print pol_read
        if pol_read['cups']:
            tots.append(pol_read['cups'][1])
            if not(pol_read['notificacio_email']  in mails):
                sense_not.append(pol_read['cups'][1])
    sense_not_ = len(sense_not)
    text_pnews = "\n" + 40*"=" 
    text_pnews += "\nContractes Nous des de {data_inici} (inclosa) fins a {data_fi} (no inclosa): {sol_pol}"
    for a in tots:
        text_pnews += "\n {a}".format(**locals())
    text_pnews += "\n Dels quals no ens han dit quina potencia volen: {sense_not_}"
    for a in sense_not:
        text_pnews += "\n {a}".format(**locals())
    text_pnews = text_pnews.format(**locals())
    print text_pnews

def endarrerits(tarifa,data):
    pol_obj = O.GiscedataPolissa
    sw_obj = O.GiscedataSwitching
    m101_obj = O.model('giscedata.switching.m1.01')
    days_draft_delayed = 45
    
    pol_ids = pol_obj.search([('tarifa.name','=',tarifa),
                       ('data_firma_contracte','>=',data),
                            ('state','=','esborrany')]) 
    pol_draft = len(pol_ids)   

    ## Esborranys endarrerits
    date_delayed_dt = datetime.today() - timedelta(days_draft_delayed)
    date_dealyed = datetime.strftime(date_delayed_dt,'%Y-%m-%d')
    pol_draft_delayed_ids = pol_obj.search([('id','in',pol_ids),
                                    ('data_firma_contracte','<',date_dealyed)])
    pol_reads = pol_obj.read(pol_draft_delayed_ids, ['cups'])
    cups_draft_delayed = [a['cups'][1] for a in pol_reads if a['cups']]
    text = "\nContractes en esborrany: {pol_draft}"
    text += "\nEndarrerits de {days_draft_delayed} dies"
    for a in cups_draft_delayed:
        text += "\n {a}".format(**locals())
    text = text.format(**locals())
    print text

contractesNous(tarifa, data_inici)
endarrerits(tarifa,data)
