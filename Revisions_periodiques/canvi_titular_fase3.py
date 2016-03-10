# -*- coding: utf-8 -*-
from erppeek import Client
from datetime import datetime,timedelta
import configdb

 
O = Client(**configdb.erpeek)

comp_obj = O.GiscedataLecturesComptador
lectP_obj = O.GiscedataLecturesLecturaPool
lectF_obj = O.GiscedataLecturesLectura
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
cups_obj = O.GiscedataCupsPs
mandate_obj = O.PaymentMandate
sw_obj = O.GiscedataSwitching
m101_obj = O.model('giscedata.switching.m1.01')
fact_obj = O.GiscedataFacturacioFactura

#Taules resum
errors = []
realitats = []
sense_dul = []
ab_error = []
sense_lectura_distri = []
sense_canvi_pagador = []

def resum_canvis_titular(total, realitats, sense_dul, ab_error, sense_lectura_distri,sense_canvi_pagador, errors):
    print "TOTAL DE CANVIS SOL·LICITATS: {}".format(total)
    print "CANVIS DE TITULARS REALITZATS: {}".format(len(realitats))
    print "  --> PER REVISAR: No tenien data ultima lectura, li hem posat la data d'alta: {}".format(sense_dul) 
    print "CANVIS NO REALITZATS"
    print "   ---> PERQUE NO HI HA HAGUT CANVI DE PAGADOR: {}".format(sense_canvi_pagador)
    print "   ---> PERQUE HI HA UNA FACTURA ABONADORA EN ESBORRANY: {}".format(ab_error)
    print "   ---> CANVIS REALITZATS EN EL CONTRACTE VELL. eN EL NOU NO HEM FET RE, ja que..."
    print "   ---> NO TROBEM UNA LECTURA DE DISTRIBUIDORA ANTERIOR A LA DATA DE ULTIMA LECTURA: {}".format(sense_lectura_distri)
    print "ERRORS EN EL PROCES: {}".format(len(errors))
    
    print "\n____MILLORES SCRIPT I PROCES_____"
    print "Falta:"
    print " - Eliminar modificació contractual. No s'ha de fer canvi de pagador"
    print " - Apuntar canvis fets a observacions"
    print " - Detectar si es CEFACO"
    print " - Quan no hi ha data de ultima lectura, posa data de alta"

sw_inicials_ids = sw_obj.search([('state','=','open'),
                                ('rebuig','=',False),
                                ('proces_id.name','=','M1'),
                                ('step_id.name','=','02')])
canvis_titular_ids = m101_obj.search([('canvi_titular','=','S'),
                                    ('sw_id','in',sw_inicials_ids)])
if canvis_titular_ids:
    canvis_titular_reads = m101_obj.read(canvis_titular_ids,['sw_id'])
    sw_ids = [a['sw_id'][0] for a in  canvis_titular_reads]
else:
    sw_ids = []


#Variables
vals_new = {'no_estimable':False,
            'observacions_estimacio':False,
            'pagador_sel':'titular'}
vals_old = {'lot_facturacio':False, 
            'renovacio_auto':False, 
            'active':False}

#Comptadors visuals
total = len(sw_ids)
n = 0

for sw_id in sw_ids:
    cups_name = sw_obj.read(sw_id,['cups_id'])['cups_id'][1]
    print cups_name

for sw_id in sw_ids:
    n += 1
    cups_id = sw_obj.read(sw_id,['cups_id'])['cups_id'][0]
    pol_antiga_id = pol_obj.search([('cups','=',cups_id)])[0]
    pol_antiga_read = pol_obj.read(pol_antiga_id,
        ['name','cups','data_alta','data_ultima_lectura','pagador','titular'])
    print "\nCUPS: {}".format(pol_antiga_read['cups'][1])
    print "%s/%s  POLISSA >> %s " % (n, total, pol_antiga_read['name'])
    if pol_antiga_read['titular'] == pol_antiga_read['pagador']:
        print "No hi ha canvi de pagador, no fem res"
        sense_canvi_pagador.append(pol_antiga_read['cups'][1])
        continue

    try:
        fact_draft_ids = fact_obj.search([('polissa_id','=', pol_antiga_id),
                                            ('state','=','draft'),
                                            ('type','=','out_invoice')])
        fact_draft_ab_ids = fact_obj.search([('polissa_id','=', pol_antiga_id),
                                            ('state','=','draft'),
                                            ('type','=','out_refund')])
        if fact_draft_ab_ids:
            print "Aquesta polissa te FACTURES ABONADORES EN ESBORRANY . Ids: {}".format(fact_draft_ab_ids)
            print "No fem re"
            ab_error.append(sw_obj.read(sw_id,['cups_id'])['cups_id'][1])
            continue        
        if fact_draft_ids:
            print "Aquesta polissa te FACTURES EN ESBORRANY. Ids: {}".format(fact_draft_ids)
            print "Les eliminem"
            fact_obj.unlink(fact_draft_ids,{})
            
        #Dupliquem el contracte     
        pol_nova_id = pol_obj.copy(pol_antiga_id,{}) 
        print "hem duplicat el contracte. El nou te el seguent id: {}".format(pol_nova_id)
        
        #CONTRACTE ANTIC. Canviem les dades, el donem de baixa   
        print "---------CONTRACTE VELL: {}---------".format(pol_antiga_read['name'])
        data_ultima_lectura = pol_antiga_read['data_ultima_lectura']
        if not data_ultima_lectura:
            print "NO HI HA DATA ULTIMA LECTURA! posem la data d'alta"
            data_ultima_lectura = pol_antiga_read['data_alta']
            sense_dul.append(sw_obj.read(sw_id,['cups_id'])['cups_id'][1])
        data_ultima_lectura_dt = datetime.strptime(data_ultima_lectura,'%Y-%m-%d')
        data_ultima_lectura_1 = datetime.strftime(data_ultima_lectura_dt + timedelta(+1),'%Y-%m-%d')
                
        comp_id = comp_obj.search([('polissa','=',pol_antiga_id),('active','=',True)])
        lectP_ids = lectP_obj.search([('name','>',data_ultima_lectura),('comptador','=',comp_id)])
        lectF_ids = lectF_obj.search([('name','>',data_ultima_lectura),('comptador','=',comp_id)])
        if lectF_ids or lectP_ids:
            lectP_obj.unlink(lectP_ids,{})
            lectF_obj.unlink(lectF_ids,{})          
        comp_obj.write(comp_id,{'active':False,'data_baixa':data_ultima_lectura})
        print "Donat de baixa el comptador"
        vals_old.update({'data_baixa':data_ultima_lectura_1})
        pol_obj.write([pol_antiga_id],vals_old,context={'from_baixa': True})
        print "Camps preparats per de baixa la polissa. Eliminat lot de facturacio"
        pol_obj.send_signal([pol_antiga_id],['baixa'])
        print "Donada de baixa la polissa antiga"
        lot_id = O.GiscedataFacturacioLot.search( [('state','=','obert')])
        clot_id = clot_obj.search([('polissa_id','=',pol_antiga_id),
                                    ('lot_id','=',lot_id)])
        clot_obj.unlink(clot_id,{})
        print "Polissa eliminada del lot"      
        
        #NOU CONTRACTE: activació
        pol_nova_read = pol_obj.read(pol_nova_id,['name'])     
        print "---------CONTRACTE NOU: {}---------".format(pol_nova_read['name'])
        comp_id = comp_obj.search([('polissa','=',pol_nova_id),('active','=',True)])
        lect_distri_id = lectP_obj.search([('name','<=',data_ultima_lectura),
                            ('comptador','=',comp_id),
                            ('origen_comer_id','in',(7,2,1))])
        if not(lect_distri_id):
            sense_lectura_distri.append(sw_obj.read(sw_id,['cups_id'])['cups_id'][1])
            print "No trobem cap lectura de distribuidora anterior a la data de l'ultima lectura"
            continue
        lect_distri_read = lectP_obj.read(lect_distri_id[0],['name'])
        data_distri = lect_distri_read['name']
        vals_new.update({'data_alta':data_distri})
        pagador_id = pol_obj.read(pol_nova_id,['pagador'])['pagador'][0]
        vals_new.update({'titular':pagador_id})
        pol_obj.write(pol_nova_id,vals_new)
        print "treiem el no estimable i observacions no estimable. Canviem Data Alta, titular i personada pagadora"
        pol_obj.send_signal([pol_nova_id],['validar', 'contracte'])
        print "Hem activat el contracte"
        mandate_obj.create({'reference': 'giscedata.polissa,%s' % pol_nova_id,'date': data_distri})
        print "Creat mandato"
        print "---------CAS ATR---------"
        sw_id = sw_obj.search([('cups_id','=',cups_id),
                                        ('state','=','open'),
                                        ('proces_id.name','=','M1'),
                                        ('step_id.name','=','02')])
        sw_obj.case_close(sw_id)
        print "tancat cas amb id: {}".format(sw_id[0])
        print "_______________________________"
        realitats.append(sw_id)
    except Exception, e:
        print e
        errors.append(sw_id)
        pass

if not(sw_ids):
    print "No hi ha casos a fer"
else:
    resum_canvis_titular(total, realitats, sense_dul, ab_error, sense_lectura_distri,sense_canvi_pagador, errors)
