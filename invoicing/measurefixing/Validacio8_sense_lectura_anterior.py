#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from validacio_eines import (
    es_cefaco,
    copiar_lectures,
    validar_canvis,
    buscar_errors_lot_ids,
    lazyOOOP,
    currentBatch,
    daysAgo,
    daysAfter,
    )
from consolemsg import step, success, warn, color, printStdError, error
import sys
from yamlns import namespace as ns

def bigstep(message):
    return printStdError(color('32;1',"\n:: "+message))
def smallstep(message):
    return printStdError(color('32;1',"   "+message))
def info(message):
    return printStdError(color('36;1',"   "+message))

doit = '--doit' in sys.argv

step("Connectant a l'erp") 
O = lazyOOOP()
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
search_vals = [
    ('status','like',u'No t\xe9 lectura anterior'),
    ('status','not like',u'No t\xe9 lectures entrades'),
    ('status','not like',u'incompleta'),
    ('status','not like',u'volta de comptador'),
    ('status','not like',u'Falta Lectura de tancament'),
    ('status','not like',u'maxímetre'),
    ('status','not like',u"La lectura actual és inferior a l'anterior"),
    ]

#Inicicialitzadors
res = ns()
res.polisses_resoltes_alinear_dates = []
res.resolta_un_comptador_sense_mod_lectura_copiada = []
res.cefaco= []
res.errors = []
res.final = []
res.un_comptador_sense_mod_amb_lectura_inicial_a_pool_no_resolta = []
res.data_alta_un_dia_despres_de_primera_lectura = []
res.data_alta_un_dia_abans_de_primera_lectura = []
res.un_comptador_sense_mod_amb_lectura_inicial_facturable = []
res.un_comptador_sense_mod_sense_lectura_inicial_a_pool = []
res.un_comptador_multiples_mod = []
res.multiples_modificacions_inactives = []
res.un_comptador_sense_lectura_tall = []
res.multiples_comptadors_actius = []
res.casos_normals_canvi_comptador = []
res.cx06 = []
res.m105 = []
res.sense_m105 = []

resum_templ = """\

============================================================================

Hem descartat les polisses que fa menys de 40 dies que s'ha activat el contracte
Polisses amb situació normal. Fa menys de 40 dies d'ultima lectura. TOTAL {len_casos_normals_canvi_comptador}

# POLISSES RESOLTES
- Alinear dates lectures modificacions/M1/lectures. TOTAL: {len_polisses_resoltes_alinear_dates}
    - Polisses: {polisses_resoltes_alinear_dates}
- No tenia la lectura inicial copiada a les lectures facturables. S'ha copiat des de les lectures de pool. TOTAL {len_resolta_un_comptador_sense_mod_lectura_copiada}
    - Polisses: {resolta_un_comptador_sense_mod_lectura_copiada}

# POLISSES NO RESOLTES. Filtrem per casos per facilitar l'anàlisi 
- Només te un comptador i una modificacio de contracte. 
    - Sense lectura inicial del contracte a pool en la data d'alta.
        - Data alta un dia després de la primera lectura que tenim a pool. {len_data_alta_un_dia_despres_de_primera_lectura}
            - Polisses: {data_alta_un_dia_despres_de_primera_lectura}
        - Data alta un dia abans de la primera lectura que tenim a pool. {len_data_alta_un_dia_abans_de_primera_lectura}
            - Polisses: {data_alta_un_dia_abans_de_primera_lectura}
        - Per analitzar. TOTAL: {len_un_comptador_sense_mod_sense_lectura_inicial_a_pool}
            - Polisses: {un_comptador_sense_mod_sense_lectura_inicial_a_pool}
    - Amb lectura inicial del contracte a lectures facturables. TOTAL: {len_un_comptador_sense_mod_amb_lectura_inicial_facturable}
        - Polisses: {un_comptador_sense_mod_amb_lectura_inicial_facturable}
    - Amb lectura inicial del contracte a pool pero no s'ha traspassat. TOTAL: {len_un_comptador_sense_mod_amb_lectura_inicial_a_pool_no_resolta}
        - Polisses: {un_comptador_sense_mod_amb_lectura_inicial_a_pool_no_resolta}


- Només te un comptador i multiples modificacio de contracte. TOTAL {len_un_comptador_multiples_mod}
    - Polisses: {un_comptador_multiples_mod}
    - Tenen un cas M105. TOTAL: {len_m105} Polisses: {m105}
        - D'aquests, un quants no lectura de tall. TOTAL:  {len_un_comptador_sense_lectura_tall}. Polisses: {un_comptador_sense_lectura_tall}
    - Casos que NO tenen M105.TOTAL: {len_sense_m105}. Polisses: {sense_m105}

- Múltiples comptador actius. TOTAL {len_multiples_comptadors_actius}
    - #cas 1: Els que tenen un comptador d'activa i un de reactiva
    - #cas 2: Els que tenen un comptador sense lectures
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
def isSolved(pol_id, search_vals):
    if not doit:
        warn("Resultat simulat")
        return True
    return isSolvedByMessage(pol_id, search_vals)

def isSolvedByMessage(pol_id, search_vals):
    # TODO: Use single polissa functions to speed up
    validar_canvis([pol_id])
    polissa_ids = buscar_errors_lot_ids(search_vals)
    return pol_id not in polissa_ids

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
    ]
pol_ids = buscar_errors_lot_ids(search_vals)
validar_canvis(pol_ids)
pol_ids = buscar_errors_lot_ids(search_vals)
pol_ids = pol_obj.search([
    ('id','in',pol_ids),
    ('data_alta','<',daysAgo(40)),
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
    data_alta = pol_read['data_alta']

    bigstep("{}/{}".format(n,total))
    smallstep("Polissa {}".format(pol_read['name']))
    smallstep("CUPS: {}".format(pol_read['cups'][1]))
#   smallstep("Distribuidora: {}".format(pol_read['distribuidora'][1])) --> problemes amb ascii
    try:
        if es_cefaco(pol_id):
            warn("Ja està detectada com a Reclamacio de Distribuidora")
            res.cefaco.append(pol_id)
            continue #next polissa

        cx06_ids = sw_obj.search([
            ('cups_id','=',pol_read['cups'][0]),
            ('proces_id.name','in',['C1','C2']),
            ('step_id.name','=','06'),
            ])
        if cx06_ids:
            res.cx06.append(pol_id)
            warn("Aquest CUPS té un CX06")
            continue #next polissa
        
        if daysAgo(40) < pol_read['data_ultima_lectura']:
            info("Aquesta polissa nomes fa 40 dies des de que el vem facturar. El descartem de l'estudi")
            res.casos_normals_canvi_comptador.append(pol_id)
            continue #next polissa
        
        #Busquem tots els comptadors
        # Hem de buscar si hi ha canvi de comptador! no el número de comptadors
        comp_ids = pol_read['comptadors']

        if len(comp_ids) == 1:
            info("Aquest contracte nomes te un comptador")
            
            if len(pol_read['modcontractuals_ids'])==1:
                info("Aquest contracte no té modificacions contractuals")
                info("Data d'alta: {}".format(data_alta))
                info("Data ultima factura: {}".format(pol_read['data_ultima_lectura']))

                lectF_ids = lectF_obj.search([
                    ('comptador','=',comp_ids[0]),
                    ('name','=',data_alta),
                    ])
                if lectF_ids:
                    info("Te lectura inicial del contracte en les lectures facturables")
                    step("--> Hem d'analitzar amb més profunditat aquests casos")
                    res.un_comptador_sense_mod_amb_lectura_inicial_facturable.append(pol_id)
                    continue #next polissa
                info("No te lectura inicial del contracte en les lectures facturables")

                lect_pool_ids = lectP_obj.search([
                    ('comptador','=',comp_ids[0]),
                    ('name','=',data_alta),
                    ])
                if not lect_pool_ids:
                    info("No te lectura inicial del contracte en les lectures de pool")
                    lect_pool_menys_un_dia_ids = lectP_obj.search([
                        ('comptador','=',comp_ids[0]),
                        ('name','=',daysAgo(1,data_alta)),
                        ])
                    if lect_pool_menys_un_dia_ids:
                        warn("La data d'alta és un dia més que la primera lectura")
                        res.data_alta_un_dia_despres_de_primera_lectura.append(pol_id)
                        continue #next polissa
                    lect_pool_mes_un_dia_ids = lectP_obj.search([
                        ('comptador','=',comp_ids[0]),
                        ('name','=',daysAfter(1,data_alta)),
                        ])
                    if lect_pool_mes_un_dia_ids:
                        warn("La data d'alta és un dia abans que la primera lectura")
                        res.data_alta_un_dia_abans_de_primera_lectura.append(pol_id)
                        continue #next polissa

                    step("--> Hem d'analitzar amb més profunditat aquests casos")
                    res.un_comptador_sense_mod_sense_lectura_inicial_a_pool.append(pol_id)
                    continue #next polissa
                lect_pool_read = lectP_obj.read(lect_pool_ids,['origen_id'])
                _, origen = lect_pool_read[0].get('origen_id',(False, 'Sin origen' ))
                info("Te lectural inicial del contracte en les lectures de pool. ")
                if origen.lower() == "estimada":
                    warn("Lectura Estimada!!!!")

                if doit:
                    step("Copiem la lectura")
                    copiar_lectures(lect_pool_ids[0])
                    if isSolved(pol_id, search_vals):
                        success("Polissa validada. Copiant la lectura hem resolt el problema")
                        res.resolta_un_comptador_sense_mod_lectura_copiada.append(pol_id)
                        continue #next polissa
                    else:
                        error("Copiant la lectura no s'ha resolt l'error")
                        res.un_comptador_sense_mod_amb_lectura_inicial_a_pool_no_resolta.append(pol_id)
                else:
                    step("Simulem la copia de la lectura")
                    res.resolta_un_comptador_sense_mod_lectura_copiada.append(pol_id)
                    continue #next polissa

            if len(pol_read['modcontractuals_ids'])>1:
                #TODO: we have to re-think it. The code doesn't do that we want
                info( "Aquest contracte te {} modificacions contractuals".format(len(pol_read['modcontractuals_ids'])))
                res.un_comptador_multiples_mod.append(pol_id)

                sw_ids = sw_obj.search([
                    ('cups_id','=',pol_read['cups'][0]),
                    ('state','=','done'),
                    ('proces_id.name','=','M1'),
                    ('step_id.name','=','05')
                    ,])
                if not(sw_ids):
                    res.sense_m105.append(pol_id)
                    continue #next polissa

                m105_id = m105_obj.search([
                    ('sw_id','=',sw_ids[-1]),
                    ])[0]
                data_activacio = m105_obj.read(m105_id,[
                    'data_activacio',
                    ])['data_activacio']
                #TODO: If multiple M1, stop
                info("Hem fet {} M1. Data activacio: {}".format(len(sw_ids),data_activacio))
                continue #TODO: remove it, when we code well

                lectF_post_ids = lectF_obj.search([
                    ('comptador','=',comp_ids[0]),
                    ('name','>',pol_read['data_ultima_lectura']),
                    ])

                if doit:
                    lectF_obj.unlink(lectF_post_ids,{})
                    info("S'han eliminat totes les lectures posteriors a la data_ultima_lectura : {}".format(pol_read['data_ultima_lectura']))
                else:
                    info("S'haurien eliminat totes les lectures posteriors a la data_ultima_lectura : {}".format(pol_read['data_ultima_lectura']))

                lect_ids = lectP_obj.search([
                    ('name','=',data_activacio),
                    ('comptador','=',comp_ids[0]),
                    ])
                if doit:
                    copiar_lectures(lect_ids[0])
                    info("S'han copiat les lectures de Pool a Facturebles en la data de tall: {data_activacio}".format(**locals()))
                else:
                    info("S'haurien copiat les lectures de Pool a Facturebles en la data de tall: {data_activacio}".format(**locals()))

                #Actualitzem data inicial i final de les modificacions
                # Data final mod antiga = data_activacio
                # Data inicial mod actual = data_activacio +1

                mod_antiga_ids = mod_obj.search([
                    ('id','in',pol_read['modcontractuals_ids']),
                    ('active','=',False),
                    ('data_final','>=',pol_read['data_ultima_lectura']),
                    ])

                if not(len(mod_antiga_ids) == 1):
                    warn("Hem trobat més d'una modificació inactiva despres de la data dultima lectura. No sabem quina triar")
                    res.multiples_modificacions_inactives.append(pol_id)
                    continue # next polissa
                if doit:
                    mod_obj.write(mod_antiga_ids[0],{'data_final':data_activacio})
                    info("Hem canviat la data de la modificació antiga al mateix dia que la data d'activacio: {data_activacio}".format(**locals()))
                else:
                    info("Hem canviat la data de la modificació antiga al mateix dia que la data d'activacio: {data_activacio}".format(**locals()))                 

                data_activacio_1 = daysAfter(1, data_activacio)
                
                mod_nova_ids = mod_obj.search([
                    ('id','in',pol_read['modcontractuals_ids']),
                    ('data_final','>=',pol_read['data_ultima_lectura'])])
                if doit:
                    mod_obj.write(mod_nova_ids[0],{'data_inici':data_activacio_1})
                    info("Hem canviat la data de la modificació actual un dia després que la data d'activacio: {data_activacio_1}".format(**locals()))
                else:
                    info("Hauríem canviat la data de la modificació actual un dia després que la data d'activacio: {data_activacio_1}".format(**locals()))
                
                #Anem a posar les dates correctes a les lectures en funció de les dates de les modificacions
                # 1r Anem a buscar la tarifa de la lectura
                lectF_ref_ids = lectF_obj.search([('comptador','=',comp_ids[0]),
                                            ('name','<',data_activacio)])
                periode_read = lectF_obj.read(lectF_ref_ids[0],['periode'])['periode']
                #Si es un canvi de Dh a una altra tarifa, no fem re per ara
                if 'DH' in periode_read[1]:
                    print "Revisar manualment, passa de {} a una altra tarifa".format(periode_read[1])
                    continue
                step(" 2n posem la data la nova tarifa acord amb la data inicial mod actual")
                lectF_ids = lectF_obj.search([
                    ('comptador','=',comp_ids[0]),
                    ('name','=',data_activacio),
                    ('periode','!=',periode_read[0]),
                    ])
                if doit:
                    lectF_obj.write(lectF_ids,{'name':data_activacio_1})
                    info("Hem posat les lectures facturables un dia després de la data d'activacio: {data_activacio_1}".format(**locals()))
                else:
                    info("Hauriem posat les lectures facturables un dia després de la data d'activacio: {data_activacio_1}".format(**locals()))
                           
                step("Canviem la data de lectura de la nova tarifa")
                lect_post_ids = lectP_obj.search([
                    ('name','>',data_activacio),
                    ('comptador','=',comp_ids[0]),
                    ]) 
                if  lect_post_ids:
                    if doit:
                        copiar_lectures(lect_post_ids[-1])
                        info("hem copiat les lectures de Pool posteriors a la data d'activació")
                    else:
                        info("hauriem copiat les lectures de Pool posteriors a la data d'activació")
                step("3r Mirem si te lectura de tall")
                lectF_tall_ids = lectF_obj.search([
                    ('comptador','=',comp_ids[0]),
                    ('name','=',data_activacio),
                    ('periode','=',periode_read[0]),
                    ])
                if not(lectF_tall_ids):
                    warn("ALERTA, no te lectura de tall. Tarifa: {}, data {}".format(periode_read[1],data_activacio))
                    #Crear lectura amb la suma de lectura P1 i P2 DH
                    res.un_comptador_sense_lectura_tall.append(pol_id)

                step("Validem a veure si ja no hi ha el problema")
                if doit:
                    validar_canvis([pol_id])
                    clot_ids = clot_obj.search(search_vals)
                    clot_reads = clot_obj.read(clot_ids,['polissa_id'])
                    pol_ids_v1 = sorted(list(set([clot_read['polissa_id'][0] for clot_read in clot_reads])))
                    if not(pol_id in pol_ids_v1):
                        success("Solucionada")
                        res.polisses_resoltes_alinear_dates.append(pol_id)
                    else:
                        res.m105.append(pol_id)
                else:
                    success("resultat simulat")
                    res.polisses_resoltes_alinear_dates.append(pol_id)
            continue 
        
        #detectem els comptadors de baixa   
        comp_baixa_ids = comp_obj.search([
            ('id','in',comp_ids),
            ('active','=', False),
            ])
        #Sense comptador de baixa i amb més d'un comptador
        if not (comp_baixa_ids):
            warn("Multiples comptadors actius") 
            res.multiples_comptadors_actius.append(pol_id)
            #cas 1: Els que tenen un comptador d'activa i un de reactiva
            #cas 2: Els que tenen un comptador sense lectures
            continue #next polissa

        error("Cas no considerat")
        res.final.append(pol_id)

    except Exception as e:
        res.errors.append({pol_id:e})
        raise
        error(unicode(e))

resum(res)

