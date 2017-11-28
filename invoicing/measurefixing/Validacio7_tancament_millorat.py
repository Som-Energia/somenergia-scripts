#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
from datetime import datetime, timedelta
from validacio_eines import buscar_errors_lot_ids, es_cefaco, validar_canvis, copiar_lectures
import configdb
from yamlns import namespace as ns
from consolemsg import step, success
import sys

#SCRIPT QUE SERVEIX PER DESBLOQUEJAR CASOS QUE NO TENEN LECTURA DE
# TANCAMENT DEL COMPTADOR DE BAIXA

doit = '--doit' in sys.argv

step("Connectant a l'erp")
O = Client(**configdb.erppeek)

step("Connectat")


#Objectes
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
comp_obj = O.GiscedataLecturesComptador
sw_obj = O.GiscedataSwitching
m105_obj = O.model('giscedata.switching.m1.05')
lectF_obj = O.GiscedataLecturesLectura
lectP_obj = O.GiscedataLecturesLecturaPool
imp_obj = O.GiscedataFacturacioImportacioLinia
mod_obj = O.GiscedataPolissaModcontractual

resum_templ = """\
============================================================================

# POLISSES RESOLTES

- Hem traspasat lectura de pool a lectura de facturació. TOTAL {len_polisses_resoltes_lectura_copiada}
    - Polisses: {polisses_resoltes_lectura_copiada}
- Dates de la modificacio contractual alineades amb les dates del comptador. TOTAL {len_polisses_resoltes_dates_comp_mod}
    - Polisses: {polisses_resoltes_dates_comp_mod}
- Dates de lectura alineades amb les dates del comptador. TOTAL {len_polisses_resoltes_dates_comp_lect}
    - Polisses: {polisses_resoltes_dates_comp_lect}

# POLISSES NO RESOLTES

- Reclamacio a distribuidora CEFACO. TOTAL {len_cefaco}
    - Polisses: {cefaco}

- Sense comptador de baixa. Els tancaments sempre han de tenir un comptador de baixa. TOTAL {len_sense_comptador_baixa}
    - Polisses: {sense_comptador_baixa}

- Cas no tractat, Només te un comptador. TOTAL {len_un_comptador}
    - Polisses: {un_comptador}

- Te mes d'una modificació contractual inactives. TOTAL {len_multiples_modificacions_inactive}
    - Polisses: {multiples_modificacions_inactive}

- Tenen lectures de tancament. problemes amb lectures copiades, tarifes erronies o dates amb modificacions contractuals. TOTAL {len_comptador_amb_lectura_tancament}
    - Polisses: {comptador_amb_lectura_tancament}

- Sense modificacio inactiva. TOTAL {len_sense_modificacions_inactives}
    - Polisses: {sense_modificacions_inactives}

- Tenen M105. TOTAL {len_m105_ids}
    - Polisses: {m105_ids}
- Polisses amb errors d'importacio F1 . TOTAL {len_polisses_error_f1}
    - Polisses: {polisses_error_f1}

- Casos no identificats. TOTAL {len_final}
    - Polisses: {final}

- ERRORS_________TOTAL {len_errors}
    - Polisses: {errors}
============================================================================
"""

def resum(result):
    result.update((
        ('len_'+k, len(result[k]))
        for k in result.keys()
        ))
    print (resum_templ.format(**result))

def isSolvedByMessage(pol_id, errorMessage):
    # TODO: Use single polissa functions to speed up
    validar_canvis([pol_id])
    polissa_ids = buscar_errors_lot_ids(errorMessage)
    return pol_id not in polissa_ids

def isSolved(pol_id):
    return isSolvedByMessage(pol_id, 'Falta Lectura de tancament amb data')

res = ns()

#Comptadors de polisses resoltes
res.polisses_resoltes_lectura_copiada = []
res.polisses_resoltes_dates_comp_mod = []
res.polisses_resoltes_dates_comp_lect = []
#Comptadors de polisses no resoltes
res.comptador_amb_lectura_tancament = []
res.un_comptador = []
res.sense_comptador_baixa = []
res.m105_ids = []
res.polisses_error_f1 = []
res.multiples_modificacions_inactive = []
res.sense_modificacions_inactives = []
res.final = []
res.cefaco= []
res.errors = []

step("Validant totes les polisses que tenen l'error")
pol_ids = buscar_errors_lot_ids('Falta Lectura de tancament amb data')
validar_canvis(pol_ids)
pol_ids = buscar_errors_lot_ids('Falta Lectura de tancament amb data')
pol_ids = sorted(list(set(pol_ids)))

#Comptadors visuals
total = len(pol_ids)
n = 0

for pol_id in pol_ids:
    n += 1
    pol_read = pol_obj.read(pol_id, [
        'name',
        'comptadors',
        'modcontractuals_ids',
        'tarifa',
        'distribuidora',
        'cups',
        ])
    step("{}/{}  Polissa {}".format(n, total, pol_read['name']))
    try:
        if es_cefaco(pol_id):
            print "Ja està detectada com a Reclamacio de Distribuidora"
            res.cefaco.append(pol_id)
            continue
        #Busquem tots els comptadors
        comp_ids = pol_read['comptadors']
        #Nomes te un comptador
        if len(comp_ids) == 1:
            print "Nomes te un comptador"
            res.un_comptador.append(pol_id)
            continue

        #detectem els comptadors de baixa
        comp_baixa_ids = comp_obj.search([('id','in',comp_ids),
                                        ('active','=', False)])
        #Sense comptador de baixa (no hauria de passar mai amb aquesta tipologia d'error)
        if not (comp_baixa_ids):
            print "No te comptadors de baixa"
            res.sense_comptador_baixa.append(pol_id)
            continue
        #Busquem quin es el comptador que no te data de baixa (si n'hi ha mes d'un, al passar l'script varis cops, ja és solucionarà
        comptador_sense_lectura_tancament = False
        for comp_baixa_id in comp_baixa_ids:
            comp_baixa_read = comp_obj.read(comp_baixa_id,
                                            ['active','name','data_baixa'])
            data_baixa = comp_baixa_read['data_baixa']
            lectF_ids = lectF_obj.search([('name','=',data_baixa),
                                        ('comptador','=',comp_baixa_id)])
            if not(lectF_ids):
                print "Comptador sense lectura de tancament. {}".format(comp_baixa_read['name'])
                comptador_sense_lectura_tancament = True
                break
        if not(comptador_sense_lectura_tancament):
            res.comptador_amb_lectura_tancament.append(pol_id)
            continue

        lectP_ids = lectP_obj.search([('name','=',data_baixa),
                                    ('comptador','=',comp_baixa_id)])
        #Problemes que es poden donar:
        # 1r No s'ha copiat la lectura de "pool" a "lectures"
        if lectP_ids and not(lectF_ids):
            print "Te lectura de Pool i no a lectures de facturacio, la copiem"
            copiar_lectures(lectP_ids[0])

            #Validem a veure si ja no hi ha el problema
            if isSolved(pol_id):
                success("No s'havia copiat la lectura des de Pool. Solucionada")
                res.polisses_resoltes_lectura_copiada.append(pol_id)
                continue

        # 2n No coincideixen les data de baixa de comptador amb la modificacio contratual inactiva
        mod_contractual_ids = mod_obj.search([('id','in',pol_read['modcontractuals_ids']),
                                                ('active','=',False)])
        if len(mod_contractual_ids) >1:
            print "Hi ha mes d'una modificació inactiva"
            res.multiples_modificacions_inactive.append(pol_id)
            continue
        if mod_contractual_ids:
            mod_contractual_read = mod_obj.read(mod_contractual_ids[0],
                                            ['data_inici','data_final'])
            #La data final de la modificacio contractual i
            # la data de baixa del comptador han de ser la mateixa
            if comp_baixa_read['data_baixa'] != mod_contractual_read['data_final']:
                print "Data COMPTADOR: {}".format(
                                comp_baixa_read['data_baixa'])
                print "Data MODIFICACIO: {}".format(
                                mod_contractual_read['data_final'])
                data_comptador_dt = datetime.strptime(
                                comp_baixa_read['data_baixa'],'%Y-%m-%d')
                data_modificacio_dt = datetime.strptime(
                                mod_contractual_read['data_final'],'%Y-%m-%d')
                # Les dos dates només tenen un dia de diferencia?
                if data_comptador_dt == data_modificacio_dt + timedelta(1):
                    mod_contractual_active_ids = mod_obj.search([
                            ('id','in',pol_read['modcontractuals_ids'])])
                    mod_obj.write(mod_contractual_ids[0],
                            {'data_final': comp_baixa_read['data_baixa']})
                    print "escrivim la data final a la modificacio contractual de inactiva: {}".format(comp_baixa_read['data_baixa'])
                    data_inici_dt =  datetime.strptime(comp_baixa_read['data_baixa'], '%Y-%m-%d')

                    data_inici = datetime.strftime(data_inici_dt + timedelta(1),'%Y-%m-%d')
                    for mod_contractual_active_id in mod_contractual_active_ids:
                        mod_obj.write(mod_contractual_active_id,{'data_inici': data_inici})
                        print "Escrivim data inicial modificacio contractual activa: {}".format(data_inici)

            #Validem a veure si ja no hi ha el problema
            if isSolved(pol_id):
                success("S'ha resolt alineant les dates de la modificacio i dels comptadors. Solucionada")
                res.polisses_resoltes_dates_comp_mod.append(pol_id)
                continue
        else:
            print "No te modificacions contractuals inactives"
            res.sense_modificacions_inactives.append(pol_id)
        # 3r No coincideixen les dates de baixa de comptador amb la data de les lectures per nomes un dia
        data_baixa_dt = datetime.strptime(data_baixa,'%Y-%m-%d')
        data_baixa_post = datetime.strftime(
                            data_baixa_dt + timedelta(1),'%Y-%m-%d')
        lectF_post_ids = lectF_obj.search([('name','=',data_baixa_post),
                                        ('comptador','=',comp_baixa_id)])
        if lectF_post_ids:
            print "TE LECTURES UN DIA POSTERIOR"
            lectF_obj.write(lectF_post_ids,{'name': data_baixa})

        data_baixa_prev = datetime.strftime(
                            data_baixa_dt - timedelta(1),'%Y-%m-%d')
        lectF_prev_ids = lectF_obj.search([('name','=',data_baixa_prev),
                                        ('comptador','=',comp_baixa_id)])
        if lectF_prev_ids:
            print "TE LECTURES UN DIA INFERIOR"
            lectF_obj.write(lectF_prev_ids,{'name': data_baixa})
        #Validem a veure si ja no hi ha el problema
        if isSolved(pol_id):
            success("S'ha resolts posant les dates de lectura alineades a la data de tall dels comptadors. Solucionada")
            res.polisses_resoltes_dates_comp_lect.append(pol_id)
            continue

        #4rt Errors d'importacio F1
        imp_ids = imp_obj.search([('state','=','erroni'),
                                ('cups_id','=',pol_read['cups'][0])])
        if imp_ids:
            res.polisses_error_f1.append(pol_id)
            print "IMPORTACIONS ERRONIES: {}".format(len(imp_ids))
            imp_reads = imp_obj.read(imp_ids,['info'])
            for imp_read in imp_reads:
                print " ----> " + (imp_read['info'])


        #Mirem quantes modificacions contratuals te
        mod_ids = pol_read['modcontractuals_ids']
        print "Aquest contracte te {} modificacions contractuals".format(len(mod_ids))
        sw_ids = sw_obj.search([('cups_id','=',pol_read['cups'][0]),
                                ('state','=','done'),
                                ('proces_id.name','=','M1'),
                                ('step_id.name','=','05')])
        if sw_ids:
            res.m105_ids.append(pol_id)
            print "Hem fet una M1, ja esta activada"
        res.final.append(pol_id)
        continue
        # Mirar si hi ha un F1 amb errors "data del comptador es posterior... exemple pol_id = 01986


    except Exception, e:
        res.errors.append({pol_id:e})
        print e


resum(res)

