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
        
                
def dump(polissa_id, lects, header, n):
    try:
        print "------------ {header} ------ [{polissa_id}] ---------".format(**locals())
        for idx in range(n):
            print '[{idx}] {date} {periode} {lectura} {origen}'.format(**{'idx': idx,
                                                                  'date': lects[idx]['name'],
                                                                  'periode': lects[idx]['periode'][1],
                                                                  'lectura': lects[idx]['lectura'],
                                                                  'origen': lects[idx]['origen_id'][1] })
    except Exception, e:
        pass


def payInvoice(invoice_id, rectificar):
    action = 'anullar'
    if rectificar:
        action = 'rectificar'
    wiz = O.WizardRanas.new()
    wiz_id = wiz.save()

    print "Applying {action} on {invoice_id}".format(**locals())
    return wiz._action(action,{'active_ids': [invoice_id]})


def get_contract_amount_mean(polissa_id):
    def months_between(d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)/30.0  # Aprox

    invoices_id = O.GiscedataFacturacioFactura.search([('polissa_id', '=', polissa_id),
                                                       ('type', '=', 'out_invoice')])
    invoices = O.GiscedataFacturacioFactura.read(invoices_id, ['data_inici', 'data_final', 'amount_total'])
    n_months = 0
    total_amount = 0
    for invoice in invoices:
        n_months += months_between(invoice['data_inici'], invoice['data_final'])
        total_amount += invoice['amount_total']
    return total_amount/n_months



def fix_contract(polissa_id, quarantine):
    lects_id = O.GiscedataLecturesLectura.search([('comptador.polissa', '=' , polissa_id)])
    lects = O.GiscedataLecturesLectura.read(lects_id, ['name', 'periode', 'lectura', 'origen_id', 'observacions'])
    offset_ct = {'2.0A (P1)': 1, '2.1A (P1)': 1,
                 '2.0DHA (P1)': 2, '2.1DHA (P1)': 2, '2.1DHS (P1)': 2}

    dump(polissa_id, lects, None, 10)

    if len(lects) < 2:
        return

    for back_idx in reversed(range(1, 15)):
        if not lects[0]['periode'][1].startswith('2'):
            # 3.0 pending
            continue

        offset = offset_ct[lects[0]['periode'][1]]
        try:
            def check_origen(lects, n, origen):
                for idx in range(1, n+1):
                    if not lects[idx]['origen_id'][1] == origen:
                        return False
                return True

            prev_idx = back_idx*offset
            last_idx = offset + prev_idx

#            if (not lects[0]['origen_id'][1] == 'Estimada'
#                and check_origen(lects, back_idx, "Estimada")) \
            if (check_origen(lects, back_idx, "Estimada")) \
                and (((lects[0]['lectura'] >= lects[last_idx]['lectura'])
                and (lects[0]['lectura'] < lects[prev_idx]['lectura']))
                or ((offset == 2) and
                (lects[1]['lectura'] >= lects[last_idx+1]['lectura'])
                and (lects[1]['lectura'] < lects[prev_idx+1]['lectura']))):

                n_days_02 = (datetime.strptime(lects[0]['name'], '%Y-%m-%d') -
                             datetime.strptime(lects[last_idx]['name'], '%Y-%m-%d')).days

                for day_idx in range(1,back_idx+1):
                    kWh_day = (lects[0]['lectura']-lects[last_idx]['lectura'])/float(n_days_02)
                    kWh_day_db = O.GiscedataPolissa.consum_diari(polissa_id)

                    _prev_idx = offset+(back_idx-day_idx)*offset
                    _last_idx = offset+(back_idx-day_idx+1)*offset
                    n_days_12 = (datetime.strptime(lects[_prev_idx]['name'], '%Y-%m-%d') -
                                 datetime.strptime(lects[_last_idx]['name'], '%Y-%m-%d')).days

                    print '## 02:{n_days_02} 12:{n_days_12} kWh_day:{kWh_day} kWh_day_db:{kWh_day_db[P1]}'.format(**locals())
                    if (kWh_day/kWh_day_db['P1']) > 5:
                        quarantine['kWh'].append(polissa_id)

                    lect_old = lects[_prev_idx]['lectura']
                    lects[_prev_idx]['lectura'] = lects[_last_idx]['lectura']+n_days_12*kWh_day
                    observacions = u'R. %s' % lect_old
                    observacions += lects[_prev_idx]['observacions'] 
                    
                    #observacions = 'R. {lect_old}\n{observacions}'.format(**{'lect_old':lect_old,
                    #                                                         'observacions':lects[_prev_idx]['observacions'].encode("ascii")})
                    O.GiscedataLecturesLectura.write([lects[_prev_idx]['id']],
                                                     {'lectura': lects[_prev_idx]['lectura'],
                                                      'observacions': '{observacions}'.format(**locals())})

                    if offset == 2:
                        # 2.XDHA

                        kWh_day = (lects[0]['lectura']-lects[last_idx+1]['lectura'])/float(n_days_02)

                        n_days_12 = (datetime.strptime(lects[_prev_idx+1]['name'], '%Y-%m-%d') -
                                     datetime.strptime(lects[_last_idx+1]['name'], '%Y-%m-%d')).days

                        print '## 02:{n_days_02} 12:{n_days_12} kWh_day:{kWh_day} kWh_day_db:{kWh_day_db[P2]}'.format(**locals())
                        if (kWh_day/kWh_day_db['P2']) > 5:
                            quarantine['kWh'].append(polissa_id)

                        lect_old = lects[_prev_idx+1]['lectura']
                        lects[_prev_idx+1]['lectura'] = lects[_last_idx+1]['lectura']+n_days_12*kWh_day
                        observacions = 'R. {lect_old}\n{observacions}'.format(**{'lect_old':lect_old,
                                                                                 'observacions':lects[_prev_idx+1]['observacions'].encode("ascii")})
                        O.GiscedataLecturesLectura.write([lects[_prev_idx+1]['id']],
                                                         {'lectura': lects[_prev_idx+1]['lectura'],
                                                          'observacions': '{observacions}'.format(**locals())})

                    dump(polissa_id, lects, 'Fixed', 10)
                    invoice_date_end = lects[_prev_idx]['name']
                    invoice_date_start = lects[_last_idx]['name']
                    invoice_rectified_id = O.GiscedataFacturacioFactura.search([('polissa_id', '=', polissa_id),
                                                                                        ('type', '=', 'out_invoice'),
                                                                                        ('data_final', '=', invoice_date_end),
                                                                                        ('data_inici', '=', invoice_date_start)])

                    if not invoice_rectified_id:
                        invoice_date_start = datetime.strftime(datetime.strptime(lects[_last_idx]['name'],
                                                                                 '%Y-%m-%d') + timedelta(days=1), '%Y-%m-%d')
                        invoice_rectified_id = O.GiscedataFacturacioFactura.search([('polissa_id', '=', polissa_id),
                                                                                    ('type', '=', 'out_invoice'),
                                                                                    ('data_final', '=', invoice_date_end),
                                                                                    ('data_inici', '=', invoice_date_start)])

                    if invoice_rectified_id:
                        invoices_id = payInvoice(invoice_rectified_id[0], True)
                        if invoices_id:
                            invoices = O.GiscedataFacturacioFactura.read(invoices_id, ['amount_total'])
                            invoice_original = invoices[1]['amount_total']
                            invoice_rectified = invoices[0]['amount_total']
                            diff = invoice_original - invoice_rectified
                            print 'original: {invoice_original} rectified: {invoice_rectified} diff: {diff}'.format(**locals())

                            if diff > 2*get_contract_amount_mean(polissa_id):
                                quarantine['euro'].append(polissa_id)

        except Exception, e:
            print e
            pass
