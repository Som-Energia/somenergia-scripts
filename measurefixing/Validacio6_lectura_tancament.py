#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime, timedelta
from validacio_eines import buscar_errors_lot_ids, es_cefaco

#SCRIPT QUE SERVEIX PER DESBLOQUEJAR CASOS QUE NO TENEN LECTURA DE
# TANCAMENT DEL COMPTADOR DE BAIXA

O = OOOP(**configdb.ooop)

#Objectes
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
comp_obj = O.GiscedataLecturesComptador
lect_fact_obj = O.GiscedataLecturesLectura
lect_pool_obj = O.GiscedataLecturesLecturaPool
fact_obj = O.GiscedataFacturacioFactura
cups_obj = O.GiscedataCupsPs
mod_obj = O.GiscedataPolissaModcontractual

#constants:


#Inicicialitzadors
cefaco= []
un_comptador = []
sense_comptador_actiu = []
multiples_comptador_actiu = []
errors = []
data_diferent = []
canviats = []
sense_lectures = []
altres_casos = []
sense_comptador_baixa = []
sense_lectures_de_tall = []

comptador_diferent_data_alta_baixa = []

pol_ids = buscar_errors_lot_ids('Falta Lectura de tancament amb data')
pol_ids = sorted(list(set(pol_ids)))


#Comptadors visuals
total = len(pol_ids)
n = 0

for pol_id in pol_ids:
    n += 1
    pol_read = pol_obj.read(pol_id,
        ['name','comptadors','modcontractuals_ids','tarifa','distribuidora','cups'])
    print "%s/%s  Polissa %s" % (n, total, pol_read['name'])
    try:
        if es_cefaco(pol_id):
            print "Ja està detectada com a Reclamacio de Distribuidora" 
            cefaco.append(pol_id)
            continue
        #Busquem tots els comptadors
        comp_ids = pol_read['comptadors']
        #Nomes te un comptador
        if len(comp_ids) == 1:
            print "Nomes te un comptador"
            un_comptador.append(pol_id)
            continue
        #Mirem quantes modificacions contratuals te
        mod_ids = pol_read['modcontractuals_ids']
        print "Aquest contracte te {} modificacions contractuals".format(len(mod_ids))
        
        #detectem el comptor de baixa   
        comp_baixa_ids = comp_obj.search([('id','in',comp_ids),
                                        ('active','=', False)])
        #Sense comptador de baixa. No s'hauria de donar aquest problema
        if not (comp_baixa_ids):
            print "No te comptadors de baixa"
            sense_comptador_baixa.append(pol_id)
            continue
        
        #Agafem el primer comptador de baixa
        comp_baixa_id = comp_baixa_ids[0]
        comp_baixa_read = comp_obj.read(comp_baixa_id, ['active','name','data_baixa'])
        data_baixa_comp_baixa = comp_baixa_read['data_baixa']
        
        #Busquem el comptador d'actiu
        comp_actiu_ids = comp_obj.search([('id','in',comp_ids),('active','=', True)])
        if not(comp_actiu_ids):
            print "no te comptador d'alta"
            sense_comptador_actiu.append(pol_id)
            continue
        if len(comp_actiu_ids) >1:
            print "Te mes d'un comptador d'alta"
            multiples_comptador_actiu.append(pol_id)
            continue
        comp_actiu_id = comp_actiu_ids[0]
        comp_alta_read = comp_obj.read(comp_actiu_id, ['name','data_alta'])
        
        
        if not(comp_baixa_read['data_baixa'] == comp_alta_read['data_alta']):
            print "Els comptadors no tenen la mateixa data de baixa que d'alta"
            comptador_diferent_data_alta_baixa.append(pol_id)
            continue
        
        data_baixa_dt = datetime.strptime(data_baixa_comp_baixa,'%Y-%m-%d')
        data_baixa_bona = datetime.strftime(data_baixa_dt - timedelta(1),'%Y-%m-%d')
        
        mod_antiga_id = mod_obj.search([('active','=',False),('id','in',pol_read['modcontractuals_ids'])])[0]
        mod_antiga = mod_obj.read(mod_antiga_id,['data_final'])
        if not(mod_antiga['data_final'] == data_baixa_bona):
            print "Correcte. Data modificacio contractual diferent a la data de baixa nova"
            print "Anem a veure si el probelma és degut a la tarifa de la lectura"
            lect_fact_id = lect_fact_obj.search([('comptador','=',comp_baixa_id),
                                            ('name','=',mod_antiga['data_final'])])
            lect_read = lect_fact_obj.read(lect_fact_id,['periode'])
            if not(lect_fact_id):
               print "No te lectures amb data final de la modificacio vella"
               sense_lectures_de_tall.append(pol_id) 
               continue
            if pol_read['tarifa'][1] in lect_read[0]['periode'][1]:
                lect_ant_id = lect_fact_obj.search([('comptador','=',comp_baixa_id),
                                            ('name','<',mod_antiga['data_final'])])
                lect_ant_read = lect_fact_obj.read(lect_ant_id,['periode'])
                
                lect_pool_id = lect_pool_obj.search([('comptador','=',comp_baixa_id),
                                            ('name','=',mod_antiga['data_final'])])
                print "ESCRIVINT PERIDOES CORRECTES A LES LECTURES"
                #lect_fact_obj.write(lect_fact_id,{'periode':lect_ant_read[0]['periode'][0]})
                #lect_pool_obj.write(lect_pool_id,{'periode':lect_ant_read[0]['periode'][0]})
                #data_alta_dt = datetime.strptime(comp_alta_read['data_alta'],'%Y-%m-%d')
                #data_alta_bona = datetime.strftime(data_baixa_dt + timedelta(1),'%Y-%m-%d')
                #lect_err_id = lect_fact_obj.search([('comptador','=',comp_alta_id),
                #                            ('name','=',comp_alta_read['data_alta'])])

                
                
            data_diferent.append(pol_id)
            continue
        lect_fact_ids = lect_fact_obj.search([('comptador','=',comp_baixa_id),
                                ('name','=',data_baixa_comp_baixa)])
        for lect_fact_id in lect_fact_ids:
            lect_fbona_ids = lect_fact_obj.search([('comptador','=',comp_baixa_id),
                                ('name','=',data_baixa_bona)])
            if lect_fbona_ids:
                print "Ja existeix una lectura de facturacio a la data bona. Eliminem la erronia"
                lect_fact_obj.unlink([lect_fact_id],{})
            else:
                lect_fact_read = lect_fact_obj.read(lect_fact_id,['name'])
                lect_fact_obj.write(lect_fact_id,{'name':data_baixa_bona})
                print "Esrivim data %s a lectura facturacio" % data_baixa_bona
        
        lect_pool_ids = lect_pool_obj.search([('comptador','=',comp_baixa_id),
                                ('name','=',data_baixa_comp_baixa)])
        for lect_pool_id in lect_pool_ids:
            lect_pbona_ids = lect_pool_obj.search([('comptador','=',comp_baixa_id),
                                ('name','=',data_baixa_bona)])
            if lect_pbona_ids:
                print "Ja existeix una lectura de Pool a la data bona. Eliminem la erronia"
                lect_pool_obj.unlink([lect_pool_id],{})
            else:
                lect_pool_read = lect_pool_obj.read(lect_pool_id,['name'])
                lect_pool_obj.write(lect_pool_id,{'name':data_baixa_bona})
                print "Esrivim data %s a lectura pool" % data_baixa_bona        
        if lect_fact_ids or lect_pool_ids:
            comp_obj.write(comp_baixa_id,{'data_baixa':data_baixa_bona})
            canviats.append(pol_id)
            continue
        else:
            print "No tenia lectures de pool i de facturacio"
            sense_lectures.append(pol_id)
            continue
        altres_casos.append(pol_id)   
             
    except Exception, e:
        errors.append({pol_id:e})
        print e
        
        
#Resum del proces
print "="*76
print "POLISSES RESOLTES______________"
print "\n Polisses que hem canviat. TOTAL %s" % len(canviats)
print "Polisses: " 
print canviats
print "POLISSES NO RESOLTES______________"
print "\n Cas no tractat, Només te un comptador. TOTAL %s" % len(un_comptador)
print "Polisses: " 
print un_comptador
print "\n Sense comptador de baixa. No hauria de passar, sempre ha d'haver un comptador de baixa amb aquest error. TOTAL %s" % len(sense_comptador_baixa)
print "Polisses: " 
print sense_comptador_baixa
print "\n Sense comptador actiu. TOTAL %s" % len(sense_comptador_actiu)
print "Polisses: " 
print sense_comptador_actiu
print "\n Multiples comptadors actius. TOTAL %s" % len(multiples_comptador_actiu)
print "Polisses: " 
print multiples_comptador_actiu

print "\n Els comptadors no tenen la mateixa data de baixa que d'alta. TOTAL %s" % len(comptador_diferent_data_alta_baixa)
print "Polisses: " 
print comptador_diferent_data_alta_baixa
print "\n Data modificacio contractual diferent a la data de baixa nova. TOTAL %s" % len(data_diferent)
print "Polisses: " 
print data_diferent
print "\n No tenia lectures de Pool i de facturacio. TOTAL %s" % len(sense_lectures)
print "Polisses: " 
print sense_lectures
print "\n No te lectures amb data final de la modificacio vella. TOTAL %s" % len(sense_lectures_de_tall)
print "Polisses: " 
print sense_lectures_de_tall


print "\n Altres casos. TOTAL %s" % len(altres_casos)
print "Polisses: " 
print altres_casos


print "\n Reclamacio a distribuidora CEFACO. TOTAL %s" % len(cefaco)
print "Polisses: " 
print cefaco
print "\n ERRORS_________TOTAL %s" % len(errors)
print "Polisses: " 
print errors
print "="*76
