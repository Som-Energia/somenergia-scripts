#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
from datetime import datetime
import configdb
from validacio_eines import (
    buscar_errors_lot_ids,
    es_cefaco,
    currentBatch,
    lazyOOOP,
    )


O = lazyOOOP()

#objectes
clot_obj = O.GiscedataFacturacioContracte_lot
pol_obj = O.GiscedataPolissa
comp_obj = O.GiscedataLecturesComptador
lectP_obj = O.GiscedataLecturesLecturaPool
lectF_obj = O.GiscedataLecturesLectura
mod_obj = O.GiscedataPolissaModcontractual

#constants
lot_id = currentBatch()
MIN_DIES_FACTURAR = 20

#Taules
errors = []
tarifa_no2 = []
cefaco = []
no_te_un_comptador = []
lot_seguent = []


search_vals = [('status','like',u'No t\xe9 lectures entrades')]
pol_ids = buscar_errors_lot_ids(search_vals)
pol_ids = sorted(list(set(pol_ids)))
#Comptadors visuals
total = len(pol_ids)
n = 0

for pol_id in pol_ids:
    n += 1
    polissa_read = pol_obj.read(pol_id,
        ['name','data_alta','tarifa','comptadors','data_ultima_lectura'])
    print "\n %s/%s  POLISSA >> %s " % (n, total, polissa_read['name'])
    try:
        if es_cefaco(pol_id):
            print "Ja està detectada com a Reclamacio de Distribuidora" 
            cefaco.append(pol_id)
            continue
        lot_read = O.GiscedataFacturacioLot.read(lot_id,['data_inici'])        
        if polissa_read['data_ultima_lectura']>=lot_read['data_inici']:
            lot_seguent.append(pol_id)
            clot_id = clot_obj.search([('polissa_id','=',pol_id),
                                        ('lot_id','=',lot_id)])
            clot_obj.unlink(clot_id,{})
            pol_obj.write(pol_id, {'lot_facturacio': lot_id +1 })
            print "el posem al lot seguent"
            continue        
        
        if not(polissa_read['tarifa'][1] in ['2.0A','2.1A']):
            print "TARIFA %s. NO FEM AQUESTA TARIFA" %  polissa_read['tarifa'][1]
            tarifa_no2.append(pol_id)
            continue
        #Cerca de comptador i excepcions
        comp_ids = polissa_read['comptadors']
        if not (len(comp_ids) == 1):
            print "Te %s comptadors" % len(comp_ids)
            no_te_un_comptador.append(pol_id)
            continue


        lecturaP_id = lectP_obj.search([('comptador','=',comp_ids[0])])
        lecturaF_ids = lectF_obj.search([('comptador','=',comp_ids[0])]) 
        lecturaF_id = lectF_obj.search([('comptador','=',comp_ids[0]),
                                        ('name','=',polissa_read['data_alta'])])
        if not(lecturaP_id) and len(lecturaF_ids) == 1 and lecturaF_id:
            print polissa_read['name']
 
    except Exception, e:
        errors.append(pol_id)
        print e    

        






