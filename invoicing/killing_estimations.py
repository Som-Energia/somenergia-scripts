#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from yamlns import namespace as ns
from consolemsg import step, success, error, warn, color, printStdError
from datetime import datetime, timedelta
import sys

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

doit = 'si' in sys.argv or '--doit' in sys.argv
query = '--query' in sys.argv
success('')
if doit:
    success("Es faran canvis a les polisses (doit=True)")
else:
    success("No es faran canvis a les polisses (doit=False)")

#Objectes
pol_obj = O.GiscedataPolissa
lectF_obj = O.GiscedataLecturesLectura
pool_obj = O.GiscedataLecturesLecturaPool
comp_obj = O.GiscedataLecturesComptador
per_obj = O.GiscedataPolissaTarifaPeriodes

# Ambit de cerques de polisses:
#  * tg = 1 -->  telegestio operativa amb cch
#  * data_ultima_lectura (facturades real ) > avui - 40 (dies) --> ha facturat els ultims 40 dies
#  * no_estimable = fals --> tick de no estimable esta desactivat
#  * facturacio_potencia = icp --> self explaining
#
# per cada polissa que trobada amb la cerca anterior es mira per ordre:
#  1 comptadors actius = 1 --> si no error i fora
#  2 hi ha lectura a 'lectures' amb origen (allowed_origins) telegestio,visual [corregida],TPL [corregida],Telemesura [corregida] en data_ultima_lectura o data_alta si no hi ha data_ultima_lectura --> si no error i fora
#  3 per cada periode (A --> P1 ; DHA --> P1 i P2 ; DHS --> P1, P2 i P3)
#  3.1 cerquem les ultimes 4 (lectures_pool_ultimes) al contador actiu --> si hi han menys de 4 (lectures_pool_minimes) llavors error i fora
#  3.2 calculem els dies entre les dates llegides --> si algun  es < 20 (min_days) o > 40 (max_days) llavors error i fora
#  4 si la polissa ha arribat aqui la passarem a no estimable si el doit esta actiu

#constants de modificació
dies = 40
lectures_pool_minimes = 4
lectures_pool_ultimes = 4
min_days = 20
max_days = 40
versio = "v2.0"
allowed_origins = [
    12, # Telegestió"
    #11, # Estimada amb factor d'utilització"
    #10, # Estimada amb l'històric"
    #9, # Sense Lectura"
    #8, # Autolectura"
    #7, # Estimada"
    6, # Visual corregida"
    5, # Visual"
    4, # TPL corregida"
    3, # TPL"
    2, # Telemesura corregida"
    1, # Telemesura"
    ]
filtres = "tg=1, origens {}, minim {} lectures a pool amb distancia entre {} i {}".format(allowed_origins,lectures_pool_minimes,min_days,max_days)
missatge = "Desactivem el sistema d'estimació ja que té telegestió "
missatge += "-- [{versio}][{filtres}]".format(**locals())

def isodate(adate):
    return adate and datetime.strptime(adate,'%Y-%m-%d')

def today_minus_days(days):
    return datetime.strftime(datetime.today() - timedelta(days = days),"%Y-%m-%d")

def test_pool_measures(periode_ids,metter_id,polissa_id,res):
    for periode_id in periode_ids:
        last_pool_ids = pool_obj.search([
            ('comptador','=',metter_id),
            ('periode','=',periode_id),
            ],
            limit=lectures_pool_ultimes,
            order="name DESC")

        if len(last_pool_ids) < lectures_pool_minimes:
            warn("menys de {} lectures, trobades {}".format(
                lectures_pool_minimes,len(last_pool_ids)))
            res.too_few_measures.append(polissa_id)
            return False

        last_pool_measures = pool_obj.read(last_pool_ids,['name','lectura'])

        days = [ (isodate(first['name']) - isodate(second['name'])).days
            for first,second in zip(last_pool_measures,last_pool_measures[1:])]

        if min(days) < min_days or max(days) > max_days:
            warn("dies entre ultimes lectures de pool fora de limits {}",days)
            res.wrong_days_pool.append(polissa_id)
            return False

        measures = [ measure['lectura'] for measure in last_pool_measures]
        measures.reverse()
        for first, second in zip(measures, measures[1:]):
            if first > second:
                warn("dies entre ultimes lectures de pool no creix {}",measures)
                res.no_grown_days_pool.append(polissa_id)
                return False

    return True

def search_candidates_to_tg(measure_origins,days):
    #counters
    res = ns({
        'candidates':[],
        'bad_metters':[],
        'no_real_measures':[],
        'too_few_measures':[],
        'wrong_days_pool':[],
        'no_grown_days_pool':[],
        'errors':[],
        })

    pol_ids = pol_obj.search([
        ('tg','=','1'), # operativa amb cch
        ('data_ultima_lectura','>',today_minus_days(days)), # ultima factura a 40 dies enradera
        ('no_estimable','=',False), # estimable
        ('facturacio_potencia','=','icp'), # no maximeter
        ]) 
    totals = len(pol_ids)

    success('')
    success('Cercant candiats a passar a no estimable:')
    for counter,pol_id in enumerate(pol_ids):
        try:
            polissa = ns(pol_obj.read(pol_id,[
                "data_ultima_lectura",
                "data_alta",
                "name",
                "tarifa",
                ]))
            step("{}/{} polissa {} {}".format(counter+1,totals,polissa.name,polissa.tarifa[1]))

            metter_ids = comp_obj.search([('polissa','=',pol_id)])
            if len(metter_ids) != 1:
                warn("Numero de comptadors no contemplat")
                res.bad_metters.append(pol_id)
                continue

            search_date = polissa.data_ultima_lectura or polissa.data_alta
            measure = lectF_obj.search([
                ('comptador','=',metter_ids[0]),
                ('name','=',search_date),
                ('origen_id','in',measure_origins),
                ])
            if not measure:
                warn("Cap lectura real trobada en {}".format(search_date))
                res.no_real_measures.append(pol_id)
                continue

            per_ids = per_obj.search([
                ('tarifa','=',polissa.tarifa[0]),
                ('tipus','=','te'),
                ])

            if not test_pool_measures(per_ids,metter_ids[0],pol_id,res):
                continue

            res.candidates.append(pol_id)

        except Exception, e:
            warn("Error {}",str(e))
            res.errors.append(pol_id)

    success('')
    success("Candidats a passar a no estimable ..... {}",len(res.candidates))
    success("Comptadors malament ................... {}",len(res.bad_metters))
    success("Sense lectures reals .................. {}",len(res.no_real_measures))
    success("Menys de {} lectures a pool ............ {}",lectures_pool_minimes,len(res.too_few_measures))
    success("Dies entre lectures fora de [{}..{}] .. {}",min_days,max_days,len(res.wrong_days_pool))
    success("Dies entre lectures no creix .......... {} , {}",len(res.no_grown_days_pool),res.no_grown_days_pool)
    success("Errors ................................ {} , {}",len(res.errors),res.errors)
    if query:
        success("Candidats: {}",res.candidates)
    return res

def search_candidates_to_tg_default():
    return search_candidates_to_tg(allowed_origins,dies)

def change_to_tg(pol_ids):
    success('')
    success('Modificant polisses:')
    res = ns()
    totals = len(pol_ids)
    for counter,pol_id in enumerate(pol_ids):

        polissa = ns(pol_obj.read(pol_id,[
            "name",
            "no_estimable",
            "observacions",
            "observacions_estimacio",
            ]))
        step("{}/{} polissa {}".format(counter+1,totals,polissa.name))

        header = "[{}] ".format(str(datetime.today())[:19])

        if polissa.observacions:
            polissa.observacions = polissa.observacions.encode("utf-8")
        changes = {
            "observacions": header + missatge + "\n\n"+ (polissa.observacions or ""),
            "observacions_estimacio": header + missatge,
            "no_estimable":True,
        }
        res[pol_id] = changes
        if doit:
            pol_obj.write(pol_id,changes)
            warn("modificat")
    return res

def candidates_to_tg():
    res = search_candidates_to_tg_default()
    if not doit:
        return res
    ret = change_to_tg(res.candidates)
    success('')
    success("S'han modificat {} polisses",len(ret))
    return ret

if __name__=='__main__':
    res = candidates_to_tg()

# vim: et ts=4 sw=4
