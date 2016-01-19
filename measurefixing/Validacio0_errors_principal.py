#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime
from validacio_eines import buscar_errors_lot_ids, validar_canvis


O = OOOP(**configdb.ooop)

#Objectes
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot

lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]

def arreglar_31A(pol_ids):
    for pol_id in pol_ids:
        clot_id = clot_obj.search([('polissa_id','=',pol_id)])
        pol_read = pol_obj.read(pol_id,['name','tarifa'])
        if pol_read['tarifa'][1] == '3.1A':
            clot_obj.write(clot_id,{'skip_validation':True})


def arreglar_baixes(pol_ids):
    control = []
    for pol_id in pol_ids:
        pol_read = pol_obj.read(pol_id,['active','data_baixa'])
        if not(pol_read['active']) and pol_read['data_baixa']:
            print "Data de baixa: %s" % pol_read['data_baixa']
            clot_obj = O.GiscedataFacturacioContracte_lot
            lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
            clot_id = clot_obj.search([('polissa_id','=',pol_id),
                                        ('lot_id','=',lot_id)])
            clot_obj.unlink(clot_id)
        else:
            control.append(pol_id)
    return control
                


pol_ids = buscar_errors_lot_ids("incompleta. Falta P4,P5,P6")
arreglar_31A(pol_ids)
validar_canvis(pol_ids)


pol_ids = buscar_errors_lot_ids("cap comptador actiu")
#script arreglar_baixes(pol_ids)
#script baixes del lot__ANTIC__BO
validar_canvis(pol_ids)


pol_ids = buscar_errors_lot_ids("La lectura actual és inferior a l'anterior")
#script Sobre_estimacions.py
validar_canvis(pol_ids)

#Falta script de Sense lectura de maxímetre

pol_ids = buscar_errors_lot_ids("incompleta")
#arreglar_lectures_incompletes(pol_ids)
validar_canvis(pol_ids)


pol_ids = buscar_errors_lot_ids('Falta Lectura de tancament amb data')
#arreglar_sense_lectura_tancament(pol_ids)
#tancament_millorat
validar_canvis(pol_ids)

clot_ids = clot_obj.search([('status','like',u'No t\xe9 lectura anterior'),
                            ('status','not like',u'No t\xe9 lectures entrades'),
                            ('status','not like',u'incompleta'),
                            ('status','not like',u'volta de comptador'),
                            ('status','not like',u'Falta Lectura de tancament'),
                            ('status','not like',u'maxímetre'),
                            ('lot_id','=',lot_id)])
clot_reads = clot_obj.read(clot_ids,['polissa_id'])
pol_ids = sorted(list(set([clot_read['polissa_id'][0] for clot_read in clot_reads])))
#arreglar_sense_lectures_anteriors(pol_ids)
validar_canvis(pol_ids)

#script Sense lectures entrades (nomes al final de lot)
#facturar des del lot aquest polisses en concret (les que han canviat missatge de validar o totes)

