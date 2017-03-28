from erppeek import Client
from datetime import datetime,timedelta
import configdb
import psycopg2
import psycopg2.extras

O = Client(**configdb.erppeek)

pol_obj = O.GiscedataPolissa
sw_obj = O.GiscedataSwitching

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description="Data fins on fer l'estudi")
    parser.add_argument('-d', '--date',
        help="Escull data fins on filtrar",
        )
    return parser.parse_args()

def contractesCIF(cif,tarifa,data):
    pol_obj = O.GiscedataPolissa
    pol_ids = pol_obj.search([('titular_nif','like',cif),
                    ('tarifa','like',tarifa),
                    ('data_firma_contracte','<',data)])
    return len(pol_ids)

def contractesTarifa(tarifa,data):
    pol_obj = O.GiscedataPolissa
    sw_obj = O.GiscedataSwitching
    m101_obj = O.model('giscedata.switching.m1.01')
    days_draft_delayed = 45

    #Polisses actived
    pol_ids = pol_obj.search([('tarifa.name','like',tarifa),
                       ('data_firma_contracte','<',data)])
    sol_pol = len(pol_ids)
    pol_reads = pol_obj.read(pol_ids, ['cups'])
    pol_cups_ids = [a['cups'][0] for a in pol_reads if a['cups']]

    #Polisses inactived
    pol_inactived_ids = pol_obj.search([('cups','not in',pol_cups_ids),
                                ('tarifa.name','like',tarifa),
                                 ('active','=',False),
                                 ('data_alta','!=', False),
                                 ('data_firma_contracte','<',data)])
    pol_inac = len(pol_inactived_ids)
    per_b = round(float(pol_inac)/float(sol_pol)*100,2)

    #Polisses en esborrany
    pol_draft_ids = pol_obj.search([('id','in',pol_ids),
                                    ('state','=','esborrany')])
    pol_draft = len(pol_draft_ids)

    mails = ['tarifa3.0@somenergia.coop']
    mails.append('ccvv@somenergia.coop')
    pol_not_ids = pol_obj.search([('id','in',pol_draft_ids),
                            ('notificacio_email','not in',mails)])
    pol_not = len(pol_not_ids)
    if pol_draft:
        per_not = 1 - round(float(pol_not)/float(pol_draft)*100,2)
    else:
        per_not = "cap contracte amb esborrany"
    ## Esborranys endarrerits
    date_delayed_dt = datetime.today() - timedelta(days_draft_delayed)
    date_dealyed = datetime.strftime(date_delayed_dt,'%Y-%m-%d')
    pol_draft_delayed_ids = pol_obj.search([('id','in',pol_draft_ids),
                                    ('data_firma_contracte','<',date_dealyed)])
    if pol_draft_delayed_ids:
        pol_reads = pol_obj.read(pol_draft_delayed_ids, ['cups'])
        cups_draft_delayed = [a['cups'][1] for a in pol_reads if a['cups']]
    else:
        cups_draft_delayed = 0

    ## quants tenen el mail 3.0A al notificador
    ### Podem mirar quants n'hi ha mab C2


    #Segmentacio
    ccvv = contractesCIF('ESH',tarifa,data)
    coop = contractesCIF('ESF',tarifa,data)
    ass = contractesCIF('ESG',tarifa,data)
    admin = contractesCIF('ESP',tarifa,data)

    #Modificacions de potencia
    sw_ids = sw_obj.search([('cups_id','in',pol_cups_ids),
                            ('proces_id.name','=','M1')])
    m1_ids = m101_obj.search([('sw_id','in',sw_ids),
                             ('sollicitudadm','in',['A','N'])])
    ### tenir en compte els c2 amb canvi de potencia
    m101 = len(m1_ids)
    per_m = round(float(m101)/float(sol_pol - pol_draft)*100,2)

    #Polisses amb facturacio endarrerida
    endarrerides_ids = pol_obj.search([('facturacio_endarrerida','=',True),
                                    ('id','in',pol_ids)])
    endarrerides = len(endarrerides_ids)


    #Resum
    text_pol = 40*"=" + "\nContractes amb {tarifa}\n" + 40*"="
    text_pol += "\nSolicituds de contractes total: {sol_pol}"
    text_pol += "\n --> CCVV: {ccvv}"
    text_pol += "\n --> Cooperatives: {coop}"
    text_pol += "\n --> Associacions: {ass}"
    text_pol += "\n --> Ajuntaments: {admin}"
    text_pol += "\nContractes de baixa : {pol_inac} ({per_b}%)"
    text_pol += "\n" + 40*"=" 
    text_pol += "\nContractes en esborrany: {pol_draft}. Endarrerits de {days_draft_delayed} dies: {cups_draft_delayed}."
    text_pol += "\n --> Contractes que han demanat un M1 (mail notificador): {pol_not}({per_not})" 
    text_pol += "\nModificacions de contractes: {m101} ({per_m}%)"
    text_pol += "\nPolisses amb facturacio endarerides: {endarrerides}"
    text_pol = text_pol.format(**locals())
    print text_pol

#Contractes nous a la setmana
def contractesNous(tarifa, data_inici):
    sense_not = []
    mails = ['tarifa3.0@somenergia.coop']
    mails.append('ccvv@somenergia.coop')
    data_fi = datetime.strftime(datetime.today(),'%Y-%m-%d')
    pol_ids = pol_obj.search([('tarifa.name','like',tarifa),
                       ('data_firma_contracte','>=',data_inici),
                       ('data_firma_contracte','<',data_fi)])
    sol_pol = len(pol_ids)
    pol_reads = pol_obj.read(pol_ids,
                        ['notificacio_email','cups'])
    for pol_read in pol_reads:
        if not(pol_read['notificacio_email']  in mails):
            if pol_read['cups']:
                sense_not.append(pol_read['cups'][1])
    sense_not_ = len(sense_not)
    text_pnews = "\n" + 40*"=" 
    text_pnews += "\nContractes Nous des de {data_inici} (inclosa) fins a {data_fi} (no inclosa): {sol_pol}"
    text_pnews += "\n Dels quals no ens han dit quina potencia volen: {sense_not_}"
    for a in sense_not:
        text_pnews += "\n {a}".format(**locals())
    text_pnews = text_pnews.format(**locals())
    print text_pnews

#Contractes nous al mes.

text_evol = "No implementat"

#contractes amb tres periodes igual


#Contractes que els hi hem fet modificacio
def getPolissesM1():
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
    # TODO polissa.tarifa = {}.format.(locals**)
    sql_query = """
    select polissa.id as polissa_ids
    from giscedata_polissa as polissa
    left join giscedata_cups_ps as cups on polissa.cups = cups.id
    left join giscedata_switching as sw on sw.cups_id = cups.id
    left join giscedata_switching_step_header as swheader on swheader.sw_id = sw.id
    left join giscedata_switching_m1_01 as m101 on m101.header_id = swheader.id
    where polissa.tarifa = 7 AND
	    polissa.active =  True AND
	    polissa.state = 'activa' AND
	    m101.sollicitudadm = 'N'
    group by polissa.id
    order by polissa.id
        """
    try:
        dbcur.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        raise ex

    pol_ids = []
    for record in dbcur.fetchall():
        pol_ids.append(record['polissa_ids'])


    print pol_ids


#Analisis de porta d'entrada. Formulari?

#Contractes en 3.1A

def resum_qc(text_evol):
    from consolemsg import fail
    args = parseargs()
    if not args.date:
        fail("Introdueix una data fins on fer l'estudi")
    contractesTarifa('3.0A',args.date)
    contractesTarifa('3.1A',args.date)
    #contractesNous('3.0A','2016-04-29')
    #print "\nEvolucio de contractes mensual"
    #print 40*"="
    #print text_evol
    #getPolissesM1()


resum_qc(text_evol)

