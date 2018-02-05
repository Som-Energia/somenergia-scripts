#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from yamlns import namespace as ns
from consolemsg import step, success, error, warn, color, printStdError
from datetime import datetime, timedelta
import random
import sys

step("Connectant a l'erp")
O = Client(**configdb.erppeek)

success("Connectat")

doit = '--doit' in sys.argv
success("l'estat del doit es {}".format(doit))

per_round = 200


#Objectes
pol_obj = O.GiscedataPolissa
lectF_obj = O.GiscedataLecturesLectura
comp_obj = O.GiscedataLecturesComptador

#constants de modificació
dies = 40
versio = "v1.0"
distris = [
    '0021', # iberdrola
    #'0031', # endesa
    ]
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
filtres = "tg=1, distris {} , origens {}".format(distris, allowed_origins)
missatge = "Desactivem el sistema d'estimació ja que té telegestió "
missatge += "-- [{versio}][{filtres}]".format(**locals())


def today_minus_days(days):
    return datetime.strftime(datetime.today() - timedelta(days = days),"%Y-%m-%d")

def search_candidates_to_tg(distributors,measure_origins,days):
    #counters
    bad_metters = []
    no_real_measures = []
    with_bad_message = []
    candidates = []
    
    pol_ids = pol_obj.search([
        ('tg','=','1'), # operativa amb cch
        ('data_ultima_lectura','>',today_minus_days(days)), # ultima factura a 40 dies enradera
        ('distribuidora.ref','in',distributors), # allowed distris
        ('no_estimable','=',False), # estimable
        ]) 
    totals = len(pol_ids)
    random.shuffle(pol_ids)
    for counter,pol_id in enumerate(pol_ids):

        if counter > per_round:
            break;

        polissa = ns(pol_obj.read(pol_id,[
            "data_ultima_lectura",
            "data_alta",
            "name",
            "observacions_estimacio",
            ]))
        step("{}/{} polissa {}".format(counter,totals,polissa.name))


        metter_ids = comp_obj.search([('polissa','=',pol_id)])
        if len(metter_ids) != 1:
            warn("Numero de comptadors no contemplat")
            bad_metters.append(pol_id)
            continue

        search_date = polissa.data_ultima_lectura or polissa.data_alta
        measure = lectF_obj.search([
            ('comptador','=',metter_ids[0]),
            ('name','=',search_date),
            ('origen_id','in',measure_origins),
            ])
        if not measure:
            warn("Cap lectura real trobada en {}".format(search_date))
            no_real_measures.append(pol_id)
            continue

        candidates.append(pol_id)

    warn("candiates ... {}".format(len(candidates)))
    return ns({
        'candidates':candidates,
        'bad_metters':bad_metters,
        'no_real_measures':no_real_measures,
        'bad_message':with_bad_message,
        })

def search_candidates_to_tg_default():
    return search_candidates_to_tg(distris,allowed_origins,dies)

def change_to_tg(pol_ids):

    res = ns()
    totals = len(pol_ids)
    for counter,pol_id in enumerate(pol_ids):

        polissa = ns(pol_obj.read(pol_id,[
            "name",
            "no_estimable",
            "observacions",
            "observacions_estimacio",
            ]))
        step("{}/{} polissa {}".format(counter,totals,polissa.name))

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
            warn("changed")
    return res

def candidates_to_tg():
    res = search_candidates_to_tg_default()
    pol_ids = res.candidates
    ret = change_to_tg(pol_ids)
    return ret

if __name__=='__main__':
   res = candidates_to_tg()

# vim: et ts=4 sw=4
