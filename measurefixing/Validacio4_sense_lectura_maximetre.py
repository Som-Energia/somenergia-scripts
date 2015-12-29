#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime, timedelta

O = OOOP(**configdb.ooop)

#Objectes
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
comp_obj = O.GiscedataLecturesComptador
lect_fact_obj = O.GiscedataLecturesLectura
mod_obj = O.GiscedataPolissaModcontractual
imp_obj = O.GiscedataFacturacioImportacioLinia

#Inicicialitzadors
errors = []
tarifa_3_canviats = []
tarifa_domestica = []
domestica_iberdrola = []

lot_id = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]


clot_ids = clot_obj.search([('status','like',u'No t\xe9 lectura de max\xedmetre'),
                            ('status','not like',u'No t\xe9 lectures entrades'),
                            ('status','not like',u'No t\xe9 lectura anterior'),
                            ('lot_id','=',lot_id)])
clot_reads = clot_obj.read(clot_ids,['polissa_id'])
pol_ids = [clot_read['polissa_id'][0] for clot_read in clot_reads]
pol_ids = sorted(list(set(pol_ids)))
pol_reads = pol_obj.read(pol_ids,['name','comptadors','modcontractuals_ids','tarifa','distribuidora'])

#Comptadors visuals
total = len(pol_reads)
n = 0

for pol_read in pol_reads:
    n += 1
    print "%s/%s  Polissa %s" % (n, total, pol_read['name'])
    try:
        if pol_read['tarifa'][1] != '3.0A':
            print "tarifa %s. Mirar cas a cas que els hi passa" % pol_read['tarifa'][1]
            
            #Distribuidores iberdrola o conquense
            if pol_read['distribuidora'][0] in [3695,2280]:
                domestica_iberdrola.append(pol_read['name'])
                continue
            tarifa_domestica.append(pol_read['name'])
            continue
        
        #Cerca de comptador i excepcions
        comp_ids = pol_read['comptadors']
        if not (len(comp_ids) == 1):
            print "Te %s comptadors" % len(comp_ids)
            continue
        mod_actual_id = mod_obj.search([('active','=',True),
                        ('id','in',pol_read['modcontractuals_ids'])])[0]
        data_inici_mod = mod_obj.read(mod_actual_id,['data_inici'])['data_inici']
        print data_inici_mod
        lect_fact_ids = lect_fact_obj.search([('comptador','=',comp_ids[0]),
                                            ('name','=',data_inici_mod)])
        if not(lect_fact_ids):
            print "No te lectures  l'inici de la modificació activa"
            continue
        mod_antiga_ids = mod_obj.search([('active','=',False),
                        ('id','in',pol_read['modcontractuals_ids'])])
        if not mod_antiga_ids:
            print "No te modificació antiga"
            continue
        print "canviem data de les modificacions contractuals"
        mod_obj.write(mod_antiga_ids[0],{'data_final':data_inici_mod})
        data_inici_dt = datetime.strptime(data_inici_mod,'%Y-%m-%d')
        data_inici_bona = datetime.strftime(data_inici_dt + timedelta(1),'%Y-%m-%d')
        mod_obj.write(mod_actual_id,{'data_inici':data_inici_bona})
        tarifa_3_canviats.append(pol_read['name'])
  
    except:
        errors.append(pol_read['name'])
        print "Raise Error\n"    
        
    
#Resum del proces
print "="*76
print "\n Polisses 3.0A que hem canviat. TOTAL %s" % len(tarifa_3_canviats)
print "Polisses: " 
print tarifa_3_canviats
print "\n Tarifes domèstiques. Estudiar i veure com automatitzar. TOTAL %s" % len(tarifa_domestica)
print "Polisses: " 
print tarifa_domestica
print "\n Tarifes domèstiques. Problema iberdrola o conquense amb maxímetre. Estudiar i veure com automatitzar. TOTAL %s" % len(domestica_iberdrola)
print "Polisses: " 
print domestica_iberdrola

print "\n ERRORS. TOTAL %s" % len(errors)
print "Polisses: " 
print errors
print "="*76
