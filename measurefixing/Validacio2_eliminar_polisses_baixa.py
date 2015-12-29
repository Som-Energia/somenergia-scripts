#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime, timedelta

O = OOOP(**configdb.ooop)

#Objectes
clot_obj = O.GiscedataFacturacioContracte_lot
lot_obj = O.GiscedataFacturacioLot
pol_obj = O.GiscedataPolissa

control = []

lot_id = lot_obj.search([('state','=','obert')])[0]


comptador_inactius = clot_obj.search([('status','like','cap comptador actiu'),('lot_id','=',lot_id)])

for clot_id in comptador_inactius:
    pol = clot_obj.read(clot_id,['polissa_id'])['polissa_id']
    print "POLISSA %s" % pol[1]
    pol_read = pol_obj.read(pol[0],['active','data_baixa'])
    if not(pol_read['active']) and pol_read['data_baixa']:
        print "Data de baixa: %s" % pol_read['data_baixa']
        clot_obj.unlink([clot_id])
    else:
        print "---> No esta de baixa"
        control.append(pol)
    
