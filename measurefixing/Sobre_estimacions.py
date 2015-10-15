#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime
from validacio_eines import fix_contract, es_cefaco

O = OOOP(**configdb.ooop)

#Objectes
pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
comp_obj = O.GiscedataLecturesComptador
lect_fact_obj = O.GiscedataLecturesLectura
lect_pool_obj = O.GiscedataLecturesLecturaPool
fact_obj = O.GiscedataFacturacioFactura
cups_obj = O.GiscedataCupsPs


#constants:
dif_maxima = 55

#Inicicialitzadors
lectures_copiades = []
lectures_massa_diferencia = []
sense_lectura_ref = []
sense_gir = []
sense_comptador = []
errors = []
cas_union_fenosa = []
multiples_lectures = []
volta_comptador = []
cefaco = []
noves_cefaco = []
lectures_posterior = []

search_vals = [('status','like',"La lectura actual és inferior a l'anterior")]
clot_ids = clot_obj.search(search_vals)
clot_reads = clot_obj.read(clot_ids,['polissa_id'])
pol_ids = [clot_read['polissa_id'][0] for clot_read in clot_reads]
pol_ids = sorted(list(set(pol_ids)))
pol_reads = pol_obj.read(pol_ids,['name','comptador','tarifa','data_ultima_lectura','distribuidora','lot_facturacio','cups','category_id'])

#Comptadors visuals
total = len(pol_reads)
n = 0

quarantine = {'kWh': [], 'euro': []}

for pol_read in pol_reads:
    fix_contract_ = False
    n += 1
    print "%s/%s  Polissa %s" % (n, total, pol_read['name'])
    try:
        if es_cefaco(pol_read['id']):
            print "Ja està detectada com a Reclamacio de Distribuidora" 
            cefaco.append(pol_read['name'])
            continue
        #Cerca de comptador i excepcions
        comp_id = comp_obj.search([('name','=',pol_read['comptador'])])
        comp_reads = comp_obj.read(comp_id, ['giro'])
        if not(comp_reads):
            print "No trobem comptador"
            sense_comptador.append(pol_read['name'])
            continue
        comp_read = comp_reads[0]
        if not(comp_read['giro']):
            print "No té gir de comptador"
            sense_gir.append(pol_read['name'])
            continue
        
        #Cerca de lectures problematiques
        limit_superior_consum = int(comp_read['giro'])* 9/10
        lect_search_vals = [('comptador','=',pol_read['comptador']),
                            ('consum','>',limit_superior_consum),
                            ('name','>',pol_read['data_ultima_lectura'])]
        lect_ids = lect_fact_obj.search(lect_search_vals)
        
        #Iterem per lectura problematica
        for lect_id in lect_ids:
            lectura = lect_fact_obj.get(lect_id)
            # Problemes amb lectures de Fenosa. Per ara només els filtrem
            # A sota hi ha codi de com solucionar-ho
            if lectura.lectura == 0 and pol_read['distribuidora'][0] == 2316:
                print "Cas unión fenosa de lectures 0. No fem re, la mirem en particular" 
                cas_union_fenosa.append(pol_read['name'])
                break       
            # Busquem la lectura de la data final de l'ultima factura              
            search_vals_ref = [('comptador','=',lectura.comptador.name),
                            ('tipus','=',lectura.tipus),
                            ('periode','like', lectura.periode.name),
                            ('name','=', pol_read['data_ultima_lectura'])]
            lect_ref_id = lect_fact_obj.search(search_vals_ref)[0]
            lect_ref_read = lect_fact_obj.read(lect_ref_id,['lectura'])
            
            ##BUSCAR SI TE UNA LECTURA POSTERIOR
            search_vals_post = [('comptador','=',lectura.comptador.name),
                            ('tipus','=',lectura.tipus),
                            ('periode','like', lectura.periode.name),
                            ('name','>',lectura.name),
                            ('lectura','>=',lect_ref_read['lectura'])]
            lect_post_ids = lect_pool_obj.search(search_vals_post)
            
            if lect_post_ids:
                lect_post_read = lect_pool_obj.read(lect_post_ids[0],['lectura','name'])
                lectures_posterior.append(pol_read['name'])
                print "Te lectures posteriors a Pool superiors a la ultima facturada"
                print "Eliminem les lectures posteriors i copiem la lectura del pool"
                #borrar lectures posteriors de facturacio
                search_post_fact = [('comptador','=',lectura.comptador.name),
                                    ('name','>',pol_read['data_ultima_lectura'])]
                lect_post_fact_id = lect_fact_obj.search(search_post_fact)
                lect_fact_obj.unlink(lect_post_fact_id,{})
                #Copiar lectura de pool
                ctx = {'active_id': lect_post_ids[0]}
                wiz_id = O.WizardCopiarLecturaPoolAFact.create({},ctx)
                O.WizardCopiarLecturaPoolAFact.action_copia_lectura([wiz_id], ctx)
                break
                

            lect_search_vals_mult = [('comptador','=',pol_read['comptador']),
                                ('tipus','=',lectura.tipus),
                                ('periode','like', lectura.periode.name),
                                ('name','>',pol_read['data_ultima_lectura'])]
    
            lect_mult_ids = lect_fact_obj.search(lect_search_vals_mult)
    
            if len(lect_mult_ids) > 1:
                print "Té lectures múltiples. Eliminem la penultima lectura entrada"
                # Eliminar la primera que lectura de les dues
                lect_fact_obj.unlink([lect_mult_ids[1]],{})
                multiples_lectures.append(pol_read['name'])
                
                break
                
            if not(lect_ref_read['lectura']):
                print "No trobem lectura de referencia"
                sense_lectura_ref.append(pol_read['name'])
                break
            
            lectures_dif = lect_ref_read['lectura'] - lectura.lectura
            
            # Volta de comptador si la lectura ref > 90% i lectura posterior <10%
            limit_inferior_consum = int(comp_read['giro'])* 1/10
            if lect_ref_read['lectura']>limit_superior_consum and lectura.lectura < limit_inferior_consum:
                print "volta de comptador"
                # clot_id = O.GiscedataFacturacioContracte_lot.search([('polissa_id','=',pol_read['id']),('lot_id','=',pol_read['lot_facturacio'][0])])[0]
                # write(clot_id,{'skip_validation':True'})
                volta_comptador.append(pol_read['name'])
                break
            no_consum_mensual = False
            cups_id = pol_read['cups'][0]
            cups_read = cups_obj.read(cups_id,['conany_kwh'])
            if not(cups_read):
                dif_maxima = 55.0
                no_consum_mensual =  True
            else:
                dif_maxima = cups_read['conany_kwh']/12.0
            
            if  0 < lectures_dif <= dif_maxima*1.1:
                print "Lectura copiada de l'anterior\n"
                txt = u"Lectura copiada de l'anterior, per haver fet una sobreestimació. %s \n" % lectura.lectura
                obs = txt + lectura.observacions
                #Canviem l'origen per Estimada
                vals_write = {'lectura':lect_ref_read['lectura'],
                            'origen_id':7,
                            'observacions':obs}
                lectura.write(vals_write)
                if not pol_read['name'] in lectures_copiades:
                    lectures_copiades.append(pol_read['name'])
            elif lectures_dif >= dif_maxima * 5 and not(no_consum_mensual):
                print "Possible cefaco. Diferencia de %d, superior a 5 cops el consum mensual %d kWh\n" % (lectures_dif,dif_maxima)
                pol_obj.write(pol_read['id'],{'category_id':[(4,4)]})
                noves_cefaco.append(pol_read['name']) 
            else:
                if not lectures_dif:
                    print "Ja està copiada"
                else:
                    print "Diferencia de %d, superior a %d kWh\n" % (lectures_dif,dif_maxima)
                    if not pol_read['name'] in lectures_massa_diferencia:
                        lectures_massa_diferencia.append(pol_read['name'])
                        fix_contract_ = True
                        
        #if fix_contract_ and False:
         #   fix_contract(pol_read['id'], quarantine)
        
                    
    except Exception, e:
        errors.append({pol_read['id']:e})
        print e
        
#Resum del proces
print "="*76
print "\n Polisses que hem copiat lectura. TOTAL %s" % len(lectures_copiades)
print "Polisses: " 
print lectures_copiades
print "\n Han arribat noves lectures, ja estan solucionades. TOTAL %s" % len(lectures_posterior)
print "Polisses: " 
print lectures_posterior
print "\n No hem copiat lectura per tenir massa diferencia entre lectures. TOTAL %s" % len(lectures_massa_diferencia)
print "Diferencia superior al consum mensual (consum anual /12) i inferior a cinc cops el consum mensual"
print "Polisses: " 
print lectures_massa_diferencia
print "\n Casos unión fenosa de lectura 0. TOTAL: %s" % len(cas_union_fenosa)
print "Polisses: "
print cas_union_fenosa
print "\n Polisses que han tingut error en el proces. TOTAL: %s" % len(errors)
print "Polisses: "
print errors
print "\n No hem trobat lectura de refencia. TOTAL %s" % len(sense_lectura_ref)
print "Polisses: " 
print sense_lectura_ref
print "\n No té gir. TOTAL %s" % len(sense_gir)
print "Polisses: " 
print sense_gir
print "\n No hem trobat comptador. TOTAL %s" % len(sense_comptador)
print "Polisses: " 
print sense_comptador
print "\n Lectures multiples. TOTAL %s" % len(multiples_lectures)
print "Polisses: " 
print multiples_lectures
print "\n Volta de comptador. TOTAL %s" % len(volta_comptador)
print "Polisses: " 
print volta_comptador
print "\n Reclamacio a distribuidora CEFACO. TOTAL %s" % len(cefaco)
print "Polisses: " 
print cefaco
print "\n NOVES CEFACO. TOTAL %s" % len(noves_cefaco)
print "Polisses: " 
print noves_cefaco
print "\n" + "="*76

###### CAS FENOSA
#                fact_id = fact_obj.search([('polissa_id','=',pol_read['id']),
#                                        ('data_final','=',lectura.name),
#                                        ('origin','not like','/comp')])
#                if fact_id:
#                    fact_read = fact_obj.read(fact_id[0],['energia_kwh'])
#                    consum = int(fact_read['energia_kwh'])
#                    search_vals = [('comptador','=',pol_read['comptador']),
#                                    ('consum','>',limit_superior_consum),
#                                    ('name','>',pol_read['data_ultima_lectura']),
#                                    ('name','<',lectura.name)]
#                    lect_ids = lect_fact_obj.search(search_vals)     


#search_vals = [('status','like',"incompleta")]
#clot_ids = clot_obj.search(search_vals)

#tarifa 3.1A skip validation
#Estabanell amb dh, dos comptadors

#search_vals = [('status','like',"tancament")]
#clot_ids = clot_obj.search(search_vals)
