#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from yamlns import namespace as ns
from consolemsg import step, success, error, warn, color, printStdError
from datetime import datetime, timedelta


step("Connectant a l'erp")
O = Client(**configdb.erppeek)

success("Connectat")


#Objectes
pol_obj = O.GiscedataPolissa
lectF_obj = O.GiscedataLecturesLectura
comp_obj = O.GiscedataLecturesComptador

#constants
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

def today_minus_days(days):
    return datetime.strftime(datetime.today() - timedelta(days = days),"%Y-%m-%d")

def search_candidates_to_tg(distributors,measure_origins,days):
    #counters
    bad_metters = []
    no_real_measures = []
    candidates = []
    
    pol_ids = pol_obj.search([
        ('tg','=','1'), # operativa amb cch
        ('data_ultima_lectura','>',today_minus_days(days)), # ultima factura a 40 dies enradera
        ('distribuidora.ref','in',distributors), # allowed distris
        ]) 
    totals = len(pol_ids)
    for counter,pol_id in enumerate(pol_ids):

        polissa = ns(pol_obj.read(pol_id,[
            "data_ultima_lectura",
            "data_alta",
            "name",
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
    return ns({
        'candidates':len(candidates),
        'bad_metters':len(bad_metters),
        'no_real_measures':len(no_real_measures),
        })

def search_candidates_to_tg_default():
    return search_candidates_to_tg(distris,allowed_origins,40)

def change_to_tg(pol_ids):

    totals = len(pol_ids)
    for counter,pol_id in enumerate(pol_ids):

        polissa = ns(pol_obj.read(pol_id,[
            "data_ultima_lectura",
            "data_alta",
            "name",
            ]))
        step("{}/{} polissa {}".format(counter,totals,polissa.name))

    
    
    
    
    #TODO: Escriure a observacions de la polissa: : missatge consensuat amb factura
    #TODO: no estaimble =  True
    #TODO: "observacions no estaimble": missatge consensuat amb factura
    res = ns()
    
    return res




# vim: et ts=4 sw=4
