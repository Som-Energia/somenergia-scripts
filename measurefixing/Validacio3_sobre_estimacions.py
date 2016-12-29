#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from validacio_eines import es_cefaco, validar_canvis, buscar_errors_lot_ids, copiar_lectures

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
polisses_resoltes_volta_comptador = []
cefaco = []
noves_cefaco = []
lectures_posterior = []
error_al_comptador_inactiu = []

pol_ids = buscar_errors_lot_ids("La lectura actual és inferior a l'anterior")
validar_canvis(pol_ids)
pol_ids = buscar_errors_lot_ids("La lectura actual és inferior a l'anterior")
pol_ids = sorted(list(set(pol_ids)))

#Comptadors visuals
total = len(pol_ids)
n = 0

for pol_id in pol_ids:
    n += 1
    pol_read = pol_obj.read(pol_id,
        ['name','comptador', 'comptadors','tarifa','data_ultima_lectura','distribuidora','lot_facturacio','cups','category_id'])
    print "\n %s/%s  Polissa %s" % (n, total, pol_read['name'])
    try:
        if es_cefaco(pol_id):
            print "Ja està detectada com a Reclamacio de Distribuidora" 
            cefaco.append(pol_read['name'])
            continue
        #Cerca de comptadors i excepcions
        if not(pol_read['comptadors']):
            print "No trobem comptadors"
            sense_comptador.append(pol_read['name'])
            continue
        for comp_id in pol_read['comptadors']:
            comp_read = comp_obj.read(comp_id, ['giro','name'])
            if not(comp_read['giro']):
                print "No té gir de comptador"
                sense_gir.append(pol_read['name'])
                continue

            #Cerca de lectures problematiques
            limit_superior_consum = int(comp_read['giro'])* 9/10
            lect_search_vals = [('comptador','=',comp_id),
                                ('consum','>',limit_superior_consum),
                                ('name','>=',pol_read['data_ultima_lectura'])]
            lect_ids = lect_fact_obj.search(lect_search_vals)
            if lect_ids:
                #Ja tenim identificat el comptador i lectures amb problemes
                break

            # Pot ser volta de comptador o que el comptador estigui be i l'altre sigui el que te problemes
            else:
                #VOLTA DE COMPTADOR:
                lect_sup_search_vals = [('comptador','=',comp_id),
                                    ('lectura','>',limit_superior_consum),
                                    ('name','=',pol_read['data_ultima_lectura'])]
                lect_sup_ids = lect_fact_obj.search(lect_sup_search_vals)
                limit_inferior_consum = int(comp_read['giro'])* 1/10
                lect_inf_search_vals = [('comptador','=',comp_id),
                                    ('lectura','<',limit_inferior_consum),
                                    ('name','>',pol_read['data_ultima_lectura'])]
                lect_inf_ids = lect_fact_obj.search(lect_inf_search_vals)     
                               # Volta de comptador si la lectura ref > 90% i lectura posterior <10%
                if  lect_sup_ids and lect_inf_ids:
                    print "Volta de comptador"
                    clot_id = clot_obj.search([('polissa_id','=',pol_id),
                                        ('lot_id','=',pol_read['lot_facturacio'][0])])[0]
                    clot_obj.write(clot_id,{'skip_validation':True})

                    #Validem a veure si ja no hi ha el problema
                    validar_canvis([pol_id])
                    pol_ids_v1 = buscar_errors_lot_ids("La lectura actual és inferior a l'anterior")
                    if not(pol_id in pol_ids_v1):
                        print "Volta de comptador. Solucionada"
                        polisses_resoltes_volta_comptador.append(pol_read['name'])
                        break

        #Iterem per lectura problematica
        for lect_id in lect_ids:
            #Si el comptador no és l'actiu, s'ha d'anar amb cuidado perque pot ser que li facturem malament
            if not(comp_read['name'] == pol_read['comptador']):
                print "El comptador no es l'actiu. Analitzar apart"
                error_al_comptador_inactiu.append(pol_read['name'])
                break
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
                copiar_lectures(lect_post_ids[0])
                break


            lect_search_vals_mult = [('comptador','=',comp_id),
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
                #pol_obj.write(pol_id,{'category_id':[(4,4)]})
                noves_cefaco.append(pol_read['name']) 
            else:
                if not lectures_dif:
                    print "Ja està copiada"
                else:
                    print "Diferencia de %d, superior a %d kWh\n" % (lectures_dif,dif_maxima)
                    if not pol_read['name'] in lectures_massa_diferencia:
                        lectures_massa_diferencia.append(pol_read['name'])


    except Exception, e:
        errors.append({pol_id:e})
        print e

#Resum del proces
print "="*76
print "POLISSES RESOLTES________________________________________"
print "\n Polisses que hem copiat lectura. TOTAL: {}".format(len(lectures_copiades))
print "Polisses: "
print lectures_copiades
print "\n Han arribat noves lectures, ja estan solucionades. TOTAL: {}".format(len(lectures_posterior))
print "Polisses: "
print lectures_posterior
print "\n Volta de comptador. TOTAL: {}".format(len(polisses_resoltes_volta_comptador))
print "Polisses: "
print polisses_resoltes_volta_comptador
print "POLISSES NO RESOLTES_____________________________________"
print "No hem copiat lectura per tenir massa diferencia entre lectures. TOTAL: {}".format(len(lectures_massa_diferencia))
print "Diferencia superior al consum mensual (consum anual /12) i inferior a cinc cops el consum mensual"
print "Polisses on la sobreestimacio es en el comptador actiu. TOTAL: {}".format(len(lectures_massa_diferencia))
print lectures_massa_diferencia
print "Polisses on la sobreestimacio es en el comptador inactiu. TOTAL: {}".format(len(error_al_comptador_inactiu))
print error_al_comptador_inactiu
print "Casos unión fenosa de lectura 0. TOTAL: {}".format(len(cas_union_fenosa))
print "PER ARA PASSAR A EN JOAN"
print "Polisses: "
print cas_union_fenosa
print "\n Sobreestimacions 5 cops mes gran que el seu consum. TOTAL: {}".format(len(noves_cefaco))
print "Polisses: "
print noves_cefaco
print "\n Polisses que han tingut error en el proces. TOTAL: {}".format(len(errors))
print "Polisses: "
print errors
print "No hem trobat lectura de referencia. TOTAL: {}".format(len(sense_lectura_ref))
print "Polisses: "
print sense_lectura_ref
print "No té gir. TOTAL: {}".format(len(sense_gir))
print "Polisses: "
print sense_gir
print "No hem trobat comptador. TOTAL: {}".format(len(sense_comptador))
print "Polisses: "
print sense_comptador
print "Lectures multiples. TOTAL: {}".format(len(multiples_lectures))
print multiples_lectures
print "\n" + "="*76

###### CAS FENOSA
#                fact_id = fact_obj.search([('polissa_id','=',pol_id),
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

