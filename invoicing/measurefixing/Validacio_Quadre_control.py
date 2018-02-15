#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from validacio_eines import (
    lazyOOOP,
    currentBatch,
    endarrerides,
)

O = lazyOOOP()

#Objectes
clot_obj = O.GiscedataFacturacioContracte_lot

lot_id = currentBatch()

total = clot_obj.search([('lot_id','=',lot_id)])
finalitzats = clot_obj.search([('state','like','finalitzat'),
                               ('lot_id','=',lot_id)])
facturat = clot_obj.search([('state','like','facturat'),
                               ('lot_id','=',lot_id)])
oberts = clot_obj.search([('state','like','obert'),
                               ('lot_id','=',lot_id)])
esborranys = clot_obj.search([('state','like','esborrany'),
                               ('lot_id','=',lot_id)])
apunt = clot_obj.search([('state','like','facturar'),
                               ('lot_id','=',lot_id)])



sobreestimacions = clot_obj.search([('state','=','obert'),
                                    ('status','like','volta de comptador'),
                                    ('status','not like','incompleta'),
                                    ('lot_id','=',lot_id)])
maximetre= clot_obj.search([('state','=','obert'),
                                    ('status','like','maxímetre '),
                                    ('lot_id','=',lot_id)])
superior_limit = clot_obj.search([('state','=','obert'),
                                    ('status','not like','volta de comptador'),
                                    ('status','like','superior al lími'),
                                    ('status','not like','incompleta'),
                                    ('lot_id','=',lot_id)])
incompleta = clot_obj.search([('state','=','obert'),
                                ('status','like','incompleta'),
                                ('lot_id','=',lot_id)])
no_lectures = clot_obj.search([('status','like',u'No t\xe9 lectures entrades'),
                                ('lot_id','=',lot_id)])
no_lectura_anterior = clot_obj.search([('state','=','obert'),
                            ('status','like',u'No t\xe9 lectura anterior'),
                            ('status','not like',u'No t\xe9 lectures entrades'),
                            ('status','not like',u'incompleta'),
                            ('status','not like',u'volta de comptador'),
                            ('status','not like',u'Falta Lectura de tancament'),
                            ('status','not like',u'maxímetre'),
                            ('lot_id','=',lot_id)])
comptador_inactiu = clot_obj.search([('state','=','obert'),
                                    ('status','like','cap comptador actiu'),
                                    ('lot_id','=',lot_id)])
baixa = clot_obj.search([('state','=','obert'),
                        ('status','like','Falta Lectura de tancament amb data'),
                        ('lot_id','=',lot_id)])
no_lect_max = clot_obj.search([('state','=','obert'),
                                ('status','like',u'No t\xe9 lectura de max\xedmetre'),
                                ('status','not like',u'No t\xe9 lectures entrades'),
                                ('status','not like',u'No t\xe9 lectura anterior'),
                                ('lot_id','=',lot_id)])
no_interval = clot_obj.search([('state','=','obert'),
                            ('status','like',u'No t\xe9 cap interval a facturar'),
                            ('status','not like',u'No t\xe9 lectures entrades'),
                            ('status','not like',u'No t\xe9 lectura anterior'),
                            ('lot_id','=',lot_id)])
nou_comptador_una_lectura = clot_obj.search([('state','=','obert'),
                                        ('status','like','Possible primera lecutura'),
                                        ('status','not like','volta de comptador'),
                                        ('status','not like','incompleta'),
                                        ('lot_id','=',lot_id)])
contractes_31 = clot_obj.search([('state','=','obert'),
                                 ('status','like','Falta P4,P5,P6'),
                                ('lot_id','=',lot_id)])
sense_mandato = clot_obj.search([('state','=','obert'),
                                 ('status','like','[V015]'),
                                ('lot_id','=',lot_id)])
volta_comptador = clot_obj.search([('state','=','obert'),
                                 ('status','like','[V001]'),
                                ('lot_id','=',lot_id)])
reactiva = clot_obj.search([('state','=','obert'),
                                 ('status','like','[V011]'),
                                ('lot_id','=',lot_id)])
iguals = clot_obj.search([('state','=','obert'),
                                 ('status','like','[V013]'),
                                ('lot_id','=',lot_id)])
tpl = clot_obj.search([('state','=','obert'),
                                 ('status','like','[V016]'),
                                ('lot_id','=',lot_id)])



total_errors = set(sobreestimacions + maximetre + superior_limit + no_lectures + incompleta + comptador_inactiu + baixa + no_lectura_anterior + no_interval + no_lect_max)

#Resum del proces
print "\n" + "="*76
print "TOTAL {}".format(len(total))
print "    {} Polisses facturades. D'aquestes n'hi ha d'endarrerides {}".format(len(finalitzats), len(endarrerides(finalitzats)))
print "    {} Polisses amb factures esborrany".format(len(facturat))
print "    {} Polisses amb lectures validades. Llestes per facturar".format(len(apunt))
print "    {} Polisses per validar (amb errors de validacio o no)".format(len(oberts))
print "    {} Polisses que encara no s'han validat en aquest lot".format(len(esborranys))

print "\nEndarrerits  bloquejats {}".format(len(total_errors), len(endarrerides(list(total_errors))))
print "    [V001] {} (Endarrerits: {}) - Possible volta de comptador".format(len(set(volta_comptador)), len(endarrerides(volta_comptador)))
print "    [V002] {} (Endarrerits: {}) - No té lectura anterior".format(len(set(no_lectura_anterior)), len(endarrerides(no_lectura_anterior)))
print "    [V003] {} (Endarrerits: {}) - No te Lectures".format(len(set(no_lectures)), len(endarrerides(no_lectures)))
print "    [V003] {} (Endarrerits: {}) - No te Lectures de maxímetre i si que te les altres lectures ben entrades".format(len(set(no_lect_max)), len(endarrerides(no_lect_max)))
print "    [V004] No existeix com Error"
print "    [V005] {} (Endarrerits: {}) - No té cap comptador actiu".format(len(set(comptador_inactiu)), len(endarrerides(comptador_inactiu)))
print "    [V006] {} (Endarrerits: {}) - Sobreestimacions".format(len(set(sobreestimacions)), len(endarrerides(sobreestimacions)))
print "    [V007] {} (Endarrerits: {}) - No té interval a facturar".format(len(set(no_interval)), len(endarrerides(no_interval)))
print "    [V008] No existeix com Error" 
print "    [V009] {} (Endarrerits: {}) - Excessos del 30 per cent. Maximetre".format(len(set(maximetre)), len(endarrerides(maximetre)))
print "    [V010] {} (Endarrerits: {}) - Exces del limit establert per SE".format(len(set(superior_limit)), len(endarrerides(superior_limit)))
print "    [V011] {} (Endarrerits: {}) - El consum de reactiva és superior a l'activa".format(len(set(reactiva)), len(endarrerides(reactiva)))
print "    [V012] {} (Endarrerits: {}) - Lectura incompleta. Falten periodes".format(len(set(incompleta)), len(endarrerides(incompleta)))
print "    [V012] {} (Endarrerits: {}) - Lectura incompleta. Falten periodes P4,P5,P6. Són contractes de 3.1A".format(len(set(contractes_31)), len(endarrerides(contractes_31)))
print "    [V013] {} (Endarrerits: {}) - Lectura anterior i actual són iguals".format(len(set(iguals)), len(endarrerides(iguals)))
print "    [V014] {} (Endarrerits: {}) - Falta lectura de tancament".format(len(set(baixa)), len(endarrerides(baixa)))
print "    [V015] {} (Endarrerits: {}) - Falta Mandato".format(len(set(sense_mandato)), len(endarrerides(sense_mandato)))
print "    [V016] {} (Endarrerits: {}) - Pendent de Carrega TPL".format(len(set(tpl)), len(endarrerides(tpl)))

print "    [No sé a quin codi d'error fa referencia] {} (Endarrerits: {}) - Primer lectura del nou comptador".format(len(set(nou_comptador_una_lectura)), len(endarrerides(nou_comptador_una_lectura)))
print "="*76
