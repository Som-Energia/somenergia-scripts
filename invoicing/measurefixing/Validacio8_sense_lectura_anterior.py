#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
from datetime import datetime, timedelta
from validacio_eines import  es_cefaco, copiar_lectures, validar_canvis
import configdb
from consolemsg import step, success
import sys
from yamlns import namespace as ns

step("Connectant a l'erp") 
O = Client(**configdb.erppeek)
success("Connectat")

#Objectes
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
comp_obj = O.GiscedataLecturesComptador
lectF_obj = O.GiscedataLecturesLectura
lectP_obj = O.GiscedataLecturesLecturaPool
mod_obj = O.GiscedataPolissaModcontractual
sw_obj = O.GiscedataSwitching
m105_obj = O.model('giscedata.switching.m1.05')

#constants:
lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])

#Inicicialitzadors
res = ns()
res.polisses_resoltes_alinear_dates = []
res.cefaco= []
res.errors = []
res.final = []
res.un_comptador_una_mod = []
res.un_comptador_multiples_mod = []
res.un_comptador_sense_lectura_tall = []
res.multiples_comptadors_actius = []
res.casos_normals_canvi_comptador = []
res.cx06 = []
res.m105 = []
res.sense_m105 = []

resum_templ = """\
Hem descartat les polisses que fa menys de 40 dies que s'ha activat el contracte
Polisses amb situació normal. Fa menys de 40 dies d'ultima lectura. TOTAL {len_casos_normals_canvi_comptador}

# POLISSES RESOLTES
- Alinear dates lectures modificacions/M1/lectures. TOTAL: {len_polisses_resoltes_alinear_dates}
    - Polisses: {polisses_resoltes_alinear_dates}

# POLISSES NO RESOLTES. Filtrem per casos per facilitar l'anàlisi 
- Només te un comptador i una modificacio de contracte. TOTAL {len_un_comptador_una_mod}
    - Polisses: {un_comptador_una_mod}

- Només te un comptador i multiples modificacio de contracte. TOTAL {len_un_comptador_multiples_mod}
    - Tenen un cas M105. TOTAL: {len_m105} Polisses: {m105}
        - D'aquests, un quants no lectura de tall. TOTAL:  {len_un_comptador_sense_lectura_tall}. Polisses: {un_comptador_sense_lectura_tall}
    - Casos que NO tenen M105.TOTAL: {len_sense_m105}. Polisses: {sense_m105}

- Sense comptador de baixa. TOTAL {len_multiples_comptadors_actius}
    - Polisses: {multiples_comptadors_actius}

- S'han d'analitzar més. TOTAL {len_final}
    - Polisses: {final}

- Té casos ATR amb pas 06. TOTAL {len_cx06}
    - Polisses: {cx06}

- Reclamacio a distribuidora CEFACO. TOTAL {len_cefaco}
    - Polisses: {cefaco}

- Errors de programació. TOTAL {len_errors}
    - Polisses: {errors}
============================================================================
"""

def resum(result):
    result.update((
        ('len_'+k, len(result[k]))
        for k in result.keys()
        ))
    print (resum_templ.format(**result))

step('Cerquem totes les polisses que no tenen lectura anterior')
step('i que no tinguin altres problemes: incompleta, maximetre, tancament ni sobreestimacions')
search_vals = [
    ('status','like',u'No t\xe9 lectura anterior'),
    ('status','not like',u'No t\xe9 lectures entrades'),
    ('status','not like',u'incompleta'),
    ('status','not like',u'volta de comptador'),
    ('status','not like',u'Falta Lectura de tancament'),
    ('status','not like',u'maxímetre'),
    ('status','not like',u"La lectura actual és inferior a l'anterior"), 
    ('lot_id','=',lot_id[0]),
    ]
clot_ids = clot_obj.search(search_vals)
clot_reads = clot_obj.read(clot_ids,[
    'polissa_id',
    ])
pol_ids = sorted(list(set([clot_read['polissa_id'][0] for clot_read in clot_reads])))
validar_canvis(pol_ids)
clot_ids = clot_obj.search(search_vals)
clot_reads = clot_obj.read(clot_ids,[
    'polissa_id',
    ])
pol_ids = sorted(list(set([clot_read['polissa_id'][0] for clot_read in clot_reads])))
avui_40 = datetime.strftime(datetime.today() - timedelta(40),"%Y-%m-%d")
pol_ids = pol_obj.search([
    ('id','in',pol_ids),
    ('data_alta','<',avui_40),
    ])

success("Polisses trobades")

#Comptadors visuals
total = len(pol_ids)
n = 0

for pol_id in pol_ids:
    n += 1
    pol_read = pol_obj.read(pol_id,[
        'name',
        'data_alta',
        'data_ultima_lectura',
        'comptadors',
        'modcontractuals_ids',
        'tarifa',
        'distribuidora',
        'cups',
        ])
    print "\n %s/%s  Polissa %s" % (n, total, pol_read['name'])
    try:
        if es_cefaco(pol_id):
            print "Ja està detectada com a Reclamacio de Distribuidora" 
            res.cefaco.append(pol_id)
            continue
        sw_ids = sw_obj.search([('cups_id','=',pol_read['cups'][0]),
                                ('proces_id.name','in',['C1','C2']),
                                ('step_id.name','=','06')])
        if sw_ids:
            res.cx06.append(pol_id)
            print "Aquest CUPS té un CX06"
            continue
        
        #Busquem tots els comptadors
        # Hem de buscar si hi ha canvi de comptador! no el número de comptadors
        comp_ids = pol_read['comptadors']
        #Nomes te un comptador
        if len(comp_ids) == 1:
            print "Nomes te un comptador"
            if len(pol_read['modcontractuals_ids'])>1:
                print "Te {} modificacions contractuals".format(len(pol_read['modcontractuals_ids']))
                res.un_comptador_multiples_mod.append(pol_id)
                sw_ids = sw_obj.search([
                    ('cups_id','=',pol_read['cups'][0]),
                    ('state','=','done'),
                    ('proces_id.name','=','M1'),
                    ('step_id.name','=','05')
                    ,])
                if not(sw_ids):
                    res.sense_m105.append(pol_id)
                    continue
                m105_id = m105_obj.search([('sw_id','=',sw_ids[-1])])[0]
                data_activacio = m105_obj.read(m105_id,['data_activacio'])['data_activacio']
                print "Hem fet {} M1. Data activacio: {}".format(len(sw_ids),
                                                            data_activacio)

                #eliminem totes les lectures de facturacio posteriors a la data de ultima lectura
                lectF_post_ids = lectF_obj.search([('comptador','=',comp_ids[0]),
                                            ('name','>',pol_read['data_ultima_lectura'])])
                lectF_obj.unlink(lectF_post_ids,{})
                print "Eliminem totes les lectures posteriors a la data_ultima_lectura : {}".format(pol_read['data_ultima_lectura'])
                
                #Copiem lectures de pool a facturacio en la data d'activació
                lect_ids = lectP_obj.search([('name','=',data_activacio),
                                        ('comptador','=',comp_ids[0])])
                copiar_lectures(lect_ids[0])
                print "Lectures copiades de Pool a Factures en la data de tall: {data_activacio}".format(**locals())
                
                #Actualitzem data inicial i final de les modificacions
                # Data final mod antiga = data_activacio
                # Data inicial mod actual = data_activacio +1
                mod_antiga_ids = mod_obj.search([
                                    ('id','in',pol_read['modcontractuals_ids']),
                                    ('active','=',False),
                                    ('data_final','>=',pol_read['data_ultima_lectura'])])
                if not(len(mod_antiga_ids) == 1):
                    print "Hem trobat més d'una modificació inactiva despres de la data dultima lectura"
                    continue
                mod_obj.write(mod_antiga_ids[0],{'data_final':data_activacio})
                data_activacio_dt = datetime.strptime(data_activacio,'%Y-%m-%d')
                data_activacio_1 = datetime.strftime(
                                    data_activacio_dt + timedelta(1),'%Y-%m-%d')
                
                mod_nova_ids = mod_obj.search([
                    ('id','in',pol_read['modcontractuals_ids']),
                    ('data_final','>=',pol_read['data_ultima_lectura'])])
                mod_obj.write(mod_nova_ids[0],{'data_inici':data_activacio_1})
                
                #Anem a posar les dates correctes a les lectures en funció de les dates de les modificacions
                # 1r Anem a buscar la tarifa de la lectura
                lectF_ref_ids = lectF_obj.search([('comptador','=',comp_ids[0]),
                                            ('name','<',data_activacio)])
                periode_read = lectF_obj.read(lectF_ref_ids[0],['periode'])['periode']
                #Si es un canvi de Dh a una altra tarifa, no fem re per ara
                if 'DH' in periode_read[1]:
                    print "Revisar manualment, passa de {} a una altra tarifa".format(periode_read[1])
                    continue
                # 2n posem la data la nova tarifa acord amb la data inicial mod actual
                lectF_ids = lectF_obj.search([
                    ('comptador','=',comp_ids[0]),
                    ('name','=',data_activacio),
                    ('periode','!=',periode_read[0]),
                    ])
                lectF_obj.write(lectF_ids,{'name':data_activacio_1})
                           
                print "Canviem la data de lectura de la nova tarifa"
                lect_post_ids = lectP_obj.search([
                    ('name','>',data_activacio),
                    ('comptador','=',comp_ids[0]),
                    ]) 
                if  lect_post_ids:
                    copiar_lectures(lect_post_ids[-1])
                    print "copiem lectures noves"        
                # 3r Mirem si te lectura de tall
                lectF_tall_ids = lectF_obj.search([
                    ('comptador','=',comp_ids[0]),
                    ('name','=',data_activacio),
                    ('periode','=',periode_read[0]),
                    ])
                if not(lectF_tall_ids):
                    print "ALERTA, no te lectura de tall. Tarifa: {}, data {}".format(periode_read[1],data_activacio)
                    #Crear lectura amb la suma de lectura P1 i P2 DH
                    res.un_comptador_sense_lectura_tall.append(pol_id)
                #Validem a veure si ja no hi ha el problema
                validar_canvis([pol_id])
                clot_ids = clot_obj.search(search_vals)
                clot_reads = clot_obj.read(clot_ids,['polissa_id'])
                pol_ids_v1 = sorted(list(set([clot_read['polissa_id'][0] for clot_read in clot_reads])))
                if not(pol_id in pol_ids_v1):
                    print "Solucionada"
                    res.polisses_resoltes_alinear_dates.append(pol_id)
                else:
                    res.m105.append(pol_id)                                
            elif len(pol_read['modcontractuals_ids'])==1:
                res.un_comptador_una_mod.append(pol_id)
            continue 
        
        #detectem els comptadors de baixa   
        comp_baixa_ids = comp_obj.search([
            ('id','in',comp_ids),
            ('active','=', False),
            ])
        #Sense comptador de baixa i amb més d'un comptador
        if not (comp_baixa_ids):
            print "Multiples comptadors actius"
            #for comp_id in comp_ids:
                
            res.multiples_comptadors_actius.append(pol_id)
            #cas 1: Els que tenen un comptador d'activa i un de reactiva
            #cas 2: Els que tenne un comptador sense lectures
            continue
        if avui_40 < pol_read['data_ultima_lectura']:
            print "Casos nous, nomes fa 40 dies de la ultima lectura"
            res.casos_normals_canvi_comptador.append(pol_id)
            continue        
        res.final.append(pol_id)
    except Exception, e:
        res.errors.append({pol_id:e})
        print e

resum(res)

