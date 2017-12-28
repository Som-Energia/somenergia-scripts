#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime,timedelta
from validacio_eines import buscar_errors_lot_ids, es_cefaco, validar_canvis, copiar_lectures
 
O = OOOP(**configdb.ooop)

#objectes
comp_obj = O.GiscedataLecturesComptador
lectP_obj = O.GiscedataLecturesLecturaPool
lectF_obj = O.GiscedataLecturesLectura
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
mod_obj = O.GiscedataPolissaModcontractual

#constants
lot_id =  O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
MIN_DIES_FACTURAR = 20

#Taules
errors = []
tarifa_no3 = []
comptadors_actius_multiples = []
comptadors_actius_multiples_mes_dun_error = []
sense_lectura_tall = []
altres_casos = []
resolts = []
cefaco = []
canvi_comptador =[]
cc_sense_posteriors = []


search_vals = [('status','like',"incompleta")]
pol_ids = buscar_errors_lot_ids(search_vals)
pol_ids = sorted(list(set(pol_ids)))
#Comptadors visuals
total = len(pol_ids)
n = 0
for pol_id in pol_ids:
    n += 1
    polissa_read = pol_obj.read(pol_id,
        ['name','data_ultima_lectura','distribuidora','comptadors','tarifa','category_id'])
    print "\n %s/%s  POLISSA >> %s" % (n, total, polissa_read['name'])
    try:
        if es_cefaco(pol_id):
            print "Ja està detectada com a Reclamacio de Distribuidora" 
            cefaco.append(pol_id)
            continue
        #No fem tarifa 3.0A ni 3.1A
        if polissa_read['tarifa'][1] in ['3.0A','3.1A']:
            print "TARIFA %s. NO FEM AQUESTA TARIFA" %  polissa_read['tarifa'][1]
            tarifa_no3.append(pol_id)
            continue
        comptador_baixa_id = comp_obj.search([('polissa','=',pol_id),
                                            ('active','=',False)])
        if len(comptador_baixa_id)>1:
            comptador_baixa_id = [comptador_baixa_id[0]]
            print "Hi ha més d'un comptador de baixa"
        comptador_alta_id = comp_obj.search([('polissa','=',pol_id)])
        if len(comptador_alta_id)>1:
            print "Hi ha més d'un comptador d'alta"
            clot_id = clot_obj.search([('polissa_id','=',pol_id),
                                        ('status','not like',u'No t\xe9 lectura anterior'),
                                        ('status','not like','volta de comptador'),
                                        ('status','not like','Falta Lectura de tancament amb data'),
                                        ('status','not like',u'No t\xe9 lectures entrades'),
                                        ('lot_id','=',lot_id)])
            if not(clot_id):
                comptadors_actius_multiples_mes_dun_error.append(pol_id)
                continue            
            clot_obj.write(clot_id,{'skip_validation': True})
            comptadors_actius_multiples.append(pol_id)
            continue

        comptador_baixa_read = comp_obj.read(comptador_baixa_id[0],['data_baixa'])
        data_tall_baixa = comptador_baixa_read['data_baixa']
        comptador_alta_read = comp_obj.read(comptador_alta_id[0],['data_alta'])
        data_tall_alta = comptador_alta_read['data_alta']
        lecturaP_tall_baixa_ids = lectP_obj.search([('comptador','=',comptador_baixa_id),
                                            ('name','=',data_tall_baixa)])
        lecturaP_tall_alta_ids = lectP_obj.search([('comptador','=',comptador_alta_id),
                                            ('name','=',data_tall_baixa)])
                                        
        mod_act_id = mod_obj.search([('polissa_id','=',pol_id)])
        mod_act_read = mod_obj.read(mod_act_id,['data_inici'])
        data_inici = mod_act_read[0]['data_inici']
        mod_inact_id = mod_obj.search([('polissa_id','=',pol_id),
                                        ('active','=',False)])
        
        # Tenen la mateixa data de tall els comptadors i tenen lectures a Pool els dos comptadors
        # 1r Problema: Falta una lectura més en el comptador nou
        if (data_tall_baixa == data_tall_alta) and lecturaP_tall_baixa_ids and lecturaP_tall_alta_ids:
            print "Es queden aturats pel nou comptador. No tenen modificacio"
            #dies_a_facturar = (datetime.strptime(data_tall_alta,'%Y-%m-%d') - datetime.strptime(polissa_read['data_ultima_lectura'],'%Y-%m-%d')).days
            #data_limit = datetime.strftime(datetime.strptime(polissa_read['data_ultima_lectura'],'%Y-%m-%d') + timedelta(MIN_DIES_FACTURAR),'%Y-%m-%d')
            #if dies_a_facturar < MIN_DIES_FACTURAR:
            lecturaP_alta_ids = lectP_obj.search([('comptador','=',comptador_alta_id),
                                                ('name','>',data_tall_alta)])
 
                # No em deixa importar la funcio de validacio_eines        
            if lecturaP_alta_ids:
                copiar_lectures(lecturaP_alta_ids[-1])  
            
            #Validem a veure si ja no hi ha el problema
            validar_canvis([pol_id])
            pol_ids_v1 = buscar_errors_lot_ids([('status','like',"incompleta")])
            if not(pol_id in pol_ids_v1):
                print "S'ha resolt. Posant una lectura mes en el comptador d'alta"
                canvi_comptador.append(pol_id)
                continue   
        
        # Tenen modificacions    
        if mod_inact_id:
            mod_inact_read = mod_obj.read(mod_inact_id,['data_final'])
            data_final = mod_inact_read[0]['data_final']
            data_final_1_dt = datetime.strptime(data_final,"%Y-%m-%d") + timedelta(1)
            data_final_1 = datetime.strftime(data_final_1_dt,"%Y-%m-%d")
            data_inici_1_dt = datetime.strptime(data_inici,"%Y-%m-%d") - timedelta(1)
            data_inici_1 = datetime.strftime(data_inici_1_dt,"%Y-%m-%d")
        
        if (data_inici_1 == data_final == data_tall_baixa == data_tall_alta) and lecturaP_tall_baixa_ids and lecturaP_tall_alta_ids:
            # En el comptador de ALTA li sumarem un dia a les lectures de tall(pool i fact) 
            # i tambe a la data de baixa del comptador
            lecturaF_tall_alta_ids = lectF_obj.search([('comptador','=',comptador_alta_id),
                                            ('name','=',data_tall_alta)])
            lectF_obj.unlink(lecturaF_tall_alta_ids,{})
            print "Hem eliminat la data de tall de facturacio del comptador de alta"
            
            lectP_obj.write(lecturaP_tall_alta_ids,{'name': data_inici})
            
            comp_obj.write(comptador_alta_id,{'data_alta':data_inici})
            print "Hem canviat data de lectures de tall i comptador de ALTA a %s" % data_inici
           
            resolts.append(pol_id)
            continue            
                            
        if (data_final_1 == data_inici == data_tall_baixa == data_tall_alta) and lecturaP_tall_baixa_ids and lecturaP_tall_alta_ids:
            # En el comptador de BAIXA li restarem un dia a les lectures de tall(pool i fact) 
            # i tambe a la data de baixa del comptador
            lecturaF_tall_baixa_ids = lectF_obj.search([('comptador','=',comptador_baixa_id),
                                            ('name','=',data_tall_baixa)])
            lectP_obj.write(lecturaP_tall_baixa_ids,{'name': data_final})
            lectF_obj.write(lecturaF_tall_baixa_ids,{'name': data_final})
            
            comp_obj.write(comptador_baixa_id,{'data_baixa':data_final})
            print "Hem canviat data de lectures de tall i comptador de baixa a %s" % data_final
            
            #eliminar lectura alta
            lecturaF_tall_alta_ids = lectF_obj.search([('comptador','=',comptador_alta_id),
                                            ('name','=',data_tall_baixa)])
            lectF_obj.unlink(lecturaF_tall_alta_ids,{})
            print "Hem eliminat la data de tall de facturacio del comptador de alta"
            resolts.append(pol_id)
            continue
        print "Altres casos no analitzats"
        altres_casos.append(pol_id)
      
    except Exception, e:
        errors.append(pol_id)
        print e




polisses_resoltes = len(resolts) + len(comptadors_actius_multiples) + len(canvi_comptador)
#Resum script
print "="*76
print "\n POLISSES RESOLTES: %d" % polisses_resoltes
print "\n Polisses resoltes. Cas en que les dates de la modificacio no concorden amb les dates dels comptadors. TOTAL %s" % len(resolts)
print "Polisses: " 
print resolts
print "\n Polisses resoltes. amb mes dun comptador actiu. RESOLTS (saltar validacio). TOTAL %s" % len(comptadors_actius_multiples)
print "Polisses: " 
print comptadors_actius_multiples
print "\n Polisses resoltes. Casos que no tenen modificacio i els hi han canviat el comptador. TOTAL %s" % len(canvi_comptador)
print "Polisses: " 
print canvi_comptador
print "\n\n POLISSES NO RESOLTES"
print "\n Polisses que han tingut error en el proces. TOTAL: %s" % len(errors)
print "Polisses: "
print errors
print "\n Polisses amb tarifa amb més d'un periode. TOTAL %s" % len(tarifa_no3)
print "Polisses: " 
print tarifa_no3
print "\n Polisses amb mes dun comptador actiu i amb mes d'un error de validacio. TOTAL %s" % len(comptadors_actius_multiples_mes_dun_error)
print "Polisses: " 
print comptadors_actius_multiples_mes_dun_error
print "\n Polisses amb comptador actiu sense lectures de tall. TOTAL %s" % len(sense_lectura_tall)
print "Polisses: " 
print sense_lectura_tall
print "\n Altres casos. Analitzar. TOTAL %s" % len(altres_casos)
print "Polisses: " 
print altres_casos
print "\n Reclamacio a distribuidora CEFACO. TOTAL %s" % len(cefaco)
print "Polisses: " 
print cefaco
print "="*76
