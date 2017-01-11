#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime,timedelta
 
O = OOOP(**configdb.ooop)

comp_obj = O.GiscedataLecturesComptador
lectP_obj = O.GiscedataLecturesLecturaPool
lectF_obj = O.GiscedataLecturesLectura
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot

#Constants
MIN_DIES_FACT = 25

def buscar_errors_lot_ids(text):
    lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
    search_vals = [('status','like',text),('lot_id','=',lot_id)]
    clot_ids = clot_obj.search(search_vals)
    clot_reads = clot_obj.read(clot_ids,['polissa_id'])
    pol_ids = sorted(list(set([clot_read['polissa_id'][0] for clot_read in clot_reads])))
    return pol_ids

def validar_canvis(pol_ids):
    lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
    search_vals = [('polissa_id','in',pol_ids),('lot_id','=',lot_id)]
    clot_ids = clot_obj.search(search_vals)
    clot_obj.wkf_obert(clot_ids,{})

def endarrerides(clot_ids):
    pol_ids = [a['polissa_id'][0] for a in clot_obj.read(clot_ids,['polissa_id'])]
    endarrerides = pol_obj.search([('facturacio_endarrerida','=',True),('id','in',pol_ids)])
    return endarrerides

def facturar_manual(pol_ids):
    #Objectes
    facturador_obj = O.GiscedataFacturacioFacturador
    factura_obj = O.GiscedataFacturacioFactura
    
    #Inicialitzadors
    polisses_names=[]
    factures_ids = []
    factures_dobles = []
    err = []
    
    polissa_ids = pol_ids
    polissa_ids = list(set(polissa_ids))
    
    avui = datetime.strftime(datetime.today(),'%Y-%m-%d')
    
    n = 0
    total = len(polissa_ids)
    
    for polissa_id in polissa_ids:
        data_fi = False
        try:
            polissa = pol_obj.get(polissa_id)
            #Només polisses amb un comptador actiu
            num_comptadors = len(comp_obj.search([('polissa','=',polissa_id)]))
            if num_comptadors==1 or True:
                comptador =  [meter for meter in polissa.comptadors if meter.active][0]
                lectures = comptador.get_lectures_per_facturar(polissa.tarifa.id)
                data_fi = max(l['actual']['name'] for l in [p for p in lectures.values()] if l)
                data_inici = (datetime.strptime(polissa.data_ultima_lectura, '%Y-%m-%d') + timedelta(days=1)).strftime( '%Y-%m-%d')
                context = {'factura_manual': True,
                        'data_inici_factura': data_inici,
                        'data_final_factura': data_fi,
                        'journal_id': 5} #Diari d'energia (code=ENERGIA de AccountJournal)
                fact_ids = facturador_obj.fact_via_lectures(polissa.id, False, context)
                factura_obj.write(fact_ids,{'date_invoice': avui})
                for fact_id in fact_ids:
                    factures_ids.append(fact_id)
                polisses_names.append(polissa.name)
                if len(fact_ids)>1:
                    factures_dobles.append(dict(polissa_id,fact_ids))
                n+=1
                print "%d/%d" % (n,total)
                print data_fi, data_inici, fact_ids
        except:
            print "polissa_id %d" % polissa_id
            err.append(polissa_id)
    return data_fi
    
def carregar_lectures_from_pool(pol_ids):
    for pol_id in pol_ids:
        comptadors_ids = O.GiscedataLecturesComptador.search([('polissa','=',pol_id)])
        ctx = {'active_ids': comptadors_ids}
        wiz_id = O.GiscedataLecturesPoolWizard.create({},ctx)
        O.GiscedataLecturesPoolWizard.action_carrega_lectures([wiz_id], ctx)
    return 
    
def adelantar_polissa_endarerida(pol_ids):
    polissa_endarerida = []
    for pol_id in pol_ids:
        carregar_lectures_from_pool([pol_id])
        data_ultima_lectura_futura = facturar_manual([pol_id])
        if not data_ultima_lectura_futura: continue
        data_limit_facturacio = datetime.strftime((datetime.today() - timedelta(MIN_DIES_FACT)),"%Y-%m-%d")
        if data_ultima_lectura_futura < data_limit_facturacio:
            polissa_endarerida.append(pol_id)
    print "polisses encara endarerides %s" % polissa_endarerida
    return

def enviar_correu(pol_id, template_id, from_id, src_model):
    print "mail enviat a la polissa{pol_id}".format(**locals())
    ctx = {'active_ids': [pol_id],'active_id': pol_id,
            'template_id': template_id, 'src_model': src_model,
            'src_rec_ids': [pol_id], 'from': from_id}
    params = {'state': 'single', 'priority':0, 'from': ctx['from']}           
    wz_id = O.PoweremailSendWizard.create(params, ctx)
    O.PoweremailSendWizard.send_mail([wz_id], ctx)

def es_cefaco(pol_id):
    pol_read = O.GiscedataPolissa.read(pol_id,['category_id'])
    return bool(set(pol_read['category_id']) & set([3,4,5,6,7]))
    
def copiar_lectures(lectura_id):
    ctx = {'active_id': lectura_id}
    wiz_id = O.WizardCopiarLecturaPoolAFact.create({},ctx)
    O.WizardCopiarLecturaPoolAFact.action_copia_lectura([wiz_id], ctx)
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
        
                
def reimportar_F1(cups_id):
    imp_obj = O.GiscedataFacturacioImportacioLinia
    wiz_obj = O.GiscedataFacturacioSwitchingWizard
    
    vals_search = [('state','=','erroni'),('cups_id','=',cups_id)]
    imp_ids = imp_obj.search(vals_search)
    for imp_id in imp_ids:
        imp_read = O.GiscedataFacturacioImportacioLinia.read(imp_id,['info'])
        ctx = {'active_id':imp_id, 'fitxer_xml': True}
        wz_id = wiz_obj.create({}, ctx)
        wiz = wiz_obj.get(wz_id)
        wiz.action_importar_f1(ctx)
        imp_new_id = O.GiscedataFacturacioImportacioLinia.read(imp_id,['info'])
        if imp_read['info'] == imp_new_id['info']:
            return False
        else:
            return True
