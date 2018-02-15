#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from validacio_eines import (
    copiar_lectures,
    lazyOOOP,
    currentBatch,
    )

O = lazyOOOP()

#Objectes
clot_obj = O.GiscedataFacturacioContracte_lot
pol_obj = O.GiscedataPolissa
lectP_obj = O.GiscedataLecturesLecturaPool
lectF_obj = O.GiscedataLecturesLectura
comp_obj = O.GiscedataLecturesComptador

control = []
nomes_te_un_comptador = []

lot_id = currentBatch()


comptador_inactius = clot_obj.search([('status','like','cap comptador actiu'),('lot_id','=',lot_id)])

for clot_id in comptador_inactius:
    pol = clot_obj.read(clot_id,['polissa_id'])['polissa_id']
    print "POLISSA %s" % pol[1]
    pol_read = pol_obj.read(pol[0],['active','data_baixa','comptadors','comptador'])
    if not(pol_read['active']) and pol_read['data_baixa']:
        print "Data de baixa: %s" % pol_read['data_baixa']
        clot_obj.unlink([clot_id])
    else:
        print "---> L'error no es que no hi hagi un comptador actiu, es que no s'ha copiat la lectura al pool"
        comp_ids = pol_read['comptadors']
        if len(comp_ids) == 1:
            print "No hi ha canvi de comptador"
            nomes_te_un_comptador.append(pol[1])
            continue
        comp_id = pol_read['comptadors'][0]
        lectura_tall = comp_obj.read(comp_id,['data_alta'])['data_alta']
        
        lectP_ids = lectP_obj.search([('name','=',lectura_tall),
                                        ('comptador','=',comp_id)])
        lectF_ids = lectF_obj.search([('name','>',lectura_tall),
                                ('comptador','=',comp_id)])
        if not(lectF_ids) and lectP_ids:
            copiar_lectures(lectP_ids[0])
            print "Hem copiat lectura de Pool a facturació"
            
            
