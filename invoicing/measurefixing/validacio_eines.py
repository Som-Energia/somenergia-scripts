#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from datetime import datetime,timedelta,date
from consolemsg import fail, success

O = None

def lazyOOOP():
    global O
    if O: return O
    O = Client(**configdb.erppeek)
    return O

#Constants
MIN_DIES_FACT = 25


def daysAgo(days, date=None):
    if date:
        date = isodate(date)
    else:
        date = datetime.today()
    return str((date - timedelta(days)).date())

def daysAfter(days, date=None):
    return daysAgo(-days, date)

def isodate(adate):
    return adate and datetime.strptime(adate,'%Y-%m-%d')

def currentBatch():
    lazyOOOP()
    Batch = O.GiscedataFacturacioLot
    return Batch.search([('state','=','obert')])[0]

def nextBatch():
    lazyOOOP()
    Batch = O.GiscedataFacturacioLot
    found = Batch.search([
        ('state','=','esborrany'),
        ],
        0, 1, 'data_inici')
    if not found:
        fail("No hi ha seguent lot creat")
    return found[0]

def showContract(pol_id):
    lazyOOOP()
    Contract = O.GiscedataPolissa
    pol_read = Contract.read(pol_id,[
        'name',
        'data_alta',
        'data_ultima_lectura',
        'comptadors',
        'modcontractuals_ids',
        'tarifa',
        'distribuidora',
        'cups',
        ])
    success("""
    Polissa: {name}
    CUPS: {cups[1]}
    Data ultima lectura: {data_ultima_lectura}
""", **pol_read)


def contractOutOfBatchDate():
    """
    Returns the contracts in the next batch
    having data_ultima_lectura before the start of
    the current batch (indeed with 6 days of buffer).
    """
    Batch = O.GiscedataFacturacioLot
    batchStartDate = Batch.read(currentBatch(), ['data_inici'])['data_inici']
    Contract = O.GiscedataPolissa
    print "Batch start date", batchStartDate
    print "Limit date", daysAgo(6,batchStartDate)
    contract_ids = Contract.search([
        ('lot_facturacio','=',nextBatch()),
        ('data_ultima_lectura', '<', daysAgo(6,batchStartDate)),
    ])
    return contract_ids


def draftContractInvoices(contract_id):
    return O.GiscedataFacturacioFactura.search([
        ('state','=','draft'),
        ('polissa_id','=',contract_id),
        ])

def buscar_errors_lot_ids(search_vals):
    lot_id = currentBatch()
    clot_obj = O.GiscedataFacturacioContracte_lot
    search_vals += [('lot_id','=',lot_id)]
    clot_ids = clot_obj.search(search_vals)
    clot_reads = clot_obj.read(clot_ids,['polissa_id'])
    pol_ids = sorted(list(set([clot_read['polissa_id'][0] for clot_read in clot_reads])))
    return pol_ids

def polissaHasError(pol_id, text):
    # TODO: test and use it instead buscar_errors_lot_ids with single polissa
    lazyOOOP()
    clot_obj = O.GiscedataFacturacioContracte_lot
    lot_id = currentBatch()
    search_vals = [
        ('status','like',text),
        ('lot_id','=',lot_id),
        ('polissa_id','=',pol_id),
        ]
    clot_ids = clot_obj.search(search_vals)
    return bool(clot_ids)

def validar_canvis(pol_ids):
    lazyOOOP()
    clot_obj = O.GiscedataFacturacioContracte_lot
    lot_id = currentBatch()
    search_vals = [('polissa_id','in',pol_ids),('lot_id','=',lot_id)]
    clot_ids = clot_obj.search(search_vals)
    clot_obj.wkf_obert(clot_ids,{})

def endarrerides(clot_ids):
    lazyOOOP()
    clot_obj = O.GiscedataFacturacioContracte_lot
    pol_obj = O.GiscedataPolissa
    pol_ids = [a['polissa_id'][0] for a in clot_obj.read(clot_ids,['polissa_id'])]
    endarrerides = pol_obj.search([
        ('facturacio_endarrerida','=',True),
        ('id','in',pol_ids),
        ])
    return endarrerides

def facturar_manual(pol_ids):
    lazyOOOP()
    #Objectes
    facturador_obj = O.GiscedataFacturacioFacturador
    factura_obj = O.GiscedataFacturacioFactura
    comp_obj = O.GiscedataLecturesComptador
    pol_obj = O.GiscedataPolissa
    
    #Inicialitzadors
    polisses_names=[]
    factures_dobles = []
    err = []
    
    polissa_ids = pol_ids
    polissa_ids = list(set(polissa_ids))
    
    avui = datetime.strftime(datetime.today(),'%Y-%m-%d')
    
    n = 0
    total = len(polissa_ids)
    
    for polissa_id in polissa_ids:
        data_fi = False
        fact_ids = []
        try:
            polissa = pol_obj.get(polissa_id)
            #Només polisses amb un comptador actiu
            num_comptadors = len(comp_obj.search([('polissa','=',polissa_id)]))
            if num_comptadors==1 or True:
                comptador =  [meter for meter in polissa.comptadors if meter.active][0]
                lectures = comptador.get_lectures_per_facturar(polissa.tarifa.id)
                data_fi = max(l['actual']['name'] for l in [p for p in lectures.values()] if l)
                if not polissa.data_ultima_lectura:
                    data_inici = polissa.data_alta
                else:
                    data_inici = (datetime.strptime(polissa.data_ultima_lectura, '%Y-%m-%d') + timedelta(days=1)).strftime( '%Y-%m-%d')
                
                context = {'factura_manual': True,
                        'data_inici_factura': data_inici,
                        'data_final_factura': data_fi,
                        'journal_id': 5} #Diari d'energia (code=ENERGIA de AccountJournal)
                fact_ids = facturador_obj.fact_via_lectures(polissa.id, False, context)
                factura_obj.write(fact_ids,{'date_invoice': avui})
                polisses_names.append(polissa.name)
                if len(fact_ids)>1:
                    factures_dobles.append(dict(polissa_id,fact_ids))
                n+=1
                print data_fi, data_inici, fact_ids
        except:
            print "polissa_id %d" % polissa_id
            err.append(polissa_id)
    return data_fi, fact_ids
    
def carregar_lectures_from_pool(pol_ids):
    lazyOOOP()
    for pol_id in pol_ids:
        comptadors_ids = O.GiscedataLecturesComptador.search([('polissa','=',pol_id)])
        if comptadors_ids == []: #Evitar error no té lectures
            print "La polissa %s no te lectures" % pol_id
            continue
        ctx = {'active_ids': comptadors_ids}
        wiz = O.GiscedataLecturesPoolWizard.create({},ctx)
        O.GiscedataLecturesPoolWizard.action_carrega_lectures([wiz.id], ctx)
    return 


def polisses_de_factures(factura_ids):
    factures = O.GiscedataFacturacioFactura.read(factura_ids, [
        'polissa_id'
        ])

    return [
        fact['polissa_id'][0]
        for fact in factures
        if fact['polissa_id']
        ]

    
def adelantar_polissa_endarerida(pol_ids):
    lazyOOOP()
    polissa_endarerida = []
    factures_ids = []
    try:
        for pol_id in pol_ids:
            print "[-] Carregant lectures a pool", pol_id
            carregar_lectures_from_pool([pol_id])

            print "[-] Facturant manualment"
            data_ultima_lectura_futura, fact_ids = facturar_manual([pol_id])
            if fact_ids:
                factures_ids.extend(fact_ids)
            if not data_ultima_lectura_futura: continue
            data_limit_facturacio = datetime.strftime((datetime.today() - timedelta(MIN_DIES_FACT)),"%Y-%m-%d")
            if data_ultima_lectura_futura < data_limit_facturacio:
                polissa_endarerida.append(pol_id)
    except Exception, e:
        print str(e)
    print "polisses encara endarerides %s" % polissa_endarerida
    print "Factures Generades. Total {}. Factures_ids: {}".format(len(factures_ids), factures_ids)
    return factures_ids

def enviar_correu(pol_id, template_id, from_id, src_model):
    lazyOOOP()
    print "mail enviat a la polissa: {pol_id}".format(**locals())
    ctx = {'active_ids': [pol_id],'active_id': pol_id,
            'template_id': template_id, 'src_model': src_model,
            'src_rec_ids': [pol_id], 'from': from_id}
    params = {'state': 'single', 'priority':0, 'from': ctx['from']}           
    wiz = O.PoweremailSendWizard.create(params, ctx)
    O.PoweremailSendWizard.send_mail([wiz.id], ctx)

def enviar_correu_actualitzacio_facturacio_endarrerida(pol_ids):
    lazyOOOP()
    pol_obj = O.GiscedataPolissa
    days = 50
    sent_email = []
    for pol_id in pol_ids:
        pol_read = pol_obj.read(pol_id,
            ['data_ultima_lectura',
            'data_alta',
            ])
        print pol_id
        data_pol = pol_read['data_ultima_lectura'] or pol_read['data_alta']
        data_ref = str(date.today()-timedelta(days=days))
        if data_pol < data_ref:
            #TODO: not id references, search for name?
            enviar_correu(pol_id,71,8,'giscedata.polissa')
            sent_email.append(pol_id)
        else:
            print "No cal enviar el correu de facturació endarrerida"
    return sent_email
 
def es_cefaco(pol_id):
    lazyOOOP()
    pol_read = O.GiscedataPolissa.read(pol_id,['category_id'])
    return bool(set(pol_read['category_id']) & set([1,3,5,6,7,8,9,14,15,21,]))
    
def copiar_lectures(lectura_id):
    lazyOOOP()
    ctx = {'active_id': lectura_id}
    wiz = O.WizardCopiarLecturaPoolAFact.create({},ctx)
    O.WizardCopiarLecturaPoolAFact.action_copia_lectura([wiz.id], ctx)
    return

def activar_modcon(pol_id, data_final):
    '''
    Activació de les modificacions contractuals estat diferent a 'Activa'
    Primer s'ha de borrar la modificació contractual actual que es l'activa.
    :param db: DB name
    :param uri: URI for connection
    :param user: User to connect
    :param password: Password to connect
    :return:
    '''
    lazyOOOP()
    search = [('polissa_id', '=', pol_id)]
    modcon_obj = O.GiscedataPolissaModcontractual
    mod_contractuals = modcon_obj.search(
        search, 0, 1, 'name desc', {'active_test': False})
    if not mod_contractuals:
        return False

    mod_id = mod_contractuals[0]
    O.GiscedataPolissa.write(
        pol_id, {'modcontractual_activa': mod_id}, {'sync': False})

    # Escrivim l'estat per tal que si hi ha modcontractual_ant vegi
    # que hem activat la següent
    modcon_obj.write(mod_id, {'state': 'actiu',
                              'data_final': data_final,
                              'active': 1},
                         {'sync': False})
    search_wkf = [('osv','=', 'giscedata.polissa.modcontractual')]
    wkf_id = O.Workflow.search(search_wkf)
    search_wkf_act = [('wkf_id', '=', wkf_id[0]),
                      ('name', '=', 'actiu')]
    wkf_activities = O.WorkflowActivity.search(search_wkf_act)

    search_wkinst = [('res_id', '=', mod_id),
                     ('res_type', '=', 'giscedata.polissa.modcontractual'),
                     ('state', '=', 'active')]
    wk_inst_id = O.WorkflowInstance.search(search_wkinst)
    search_wkitem = [('inst_id', '=', wk_inst_id[0])]
    wk_workitem_id = O.WorkflowWorkitem.search(search_wkitem)
    O.WorkflowWorkitem.write(wk_workitem_id, {'act_id': wkf_activities[0]})
    return True    
        
                
def reimportar_ok(linia_id):
    lazyOOOP()
    import time
    lin_obj = O.GiscedataFacturacioImportacioLinia
    info_inicial = lin_obj.read([linia_id],['info'])[0]['info']
    lin_obj.process_line(linia_id)
    time.sleep(15)
    lin_read = lin_obj.read([linia_id],['info','conte_factures'])
    info_nova = lin_read[0]['info']
    conte_factures = lin_read[0]['conte_factures']
    value = {'mateix_missatge':False,'ok':False}
    if lin_read[0]['conte_factures']:
        value['ok'] = True
    if info_inicial == info_nova:
        #print "informacio igual: %s" % info_inicial
        print "Mateix missatge"
        value['mateix_missatge']=True
    else:
        #print "Missatge Inicial: %s \n Missatge Final: %s" % (info_inicial,info_nova)
        print "S'ha actualitzat el missatge"
    return value

# vim: et ts=4 sw=4
