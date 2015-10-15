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

lot_id = lot_obj.search([('state','=','obert')])

total = len(clot_obj.search([('lot_id','=',lot_id)]))
finalitzats = clot_obj.search([('state','like','finalitzat'),('lot_id','=',lot_id)])
facturat = len(clot_obj.search([('state','like','facturat'),('lot_id','=',lot_id)]))
per_facturar = len(clot_obj.search([('state','like','facturar'),('lot_id','=',lot_id)]))
oberts = len(clot_obj.search([('state','like','obert'),('lot_id','=',lot_id)]))
esborranys = len(clot_obj.search([('state','like','facturat'),('lot_id','=',lot_id)]))

def endarrerides(clot_ids):
    pol_ids = [a['polissa_id'][0] for a in clot_obj.read(clot_ids,['polissa_id'])]
    endarrerides = pol_obj.search([('facturacio_endarrerida','=',True),('id','in',pol_ids)])
    return endarrerides


sobreestimacions = clot_obj.search([('status','like','volta de comptador'),('status','not like','incompleta'),('lot_id','=',lot_id)])
maximetre= clot_obj.search([('status','like','maxímetre '),('lot_id','=',lot_id)])
superior_limit = clot_obj.search([('status','not like','volta de comptador'),('status','like','superior al lími'),('status','not like','incompleta'),('lot_id','=',lot_id)])
incompleta = clot_obj.search([('status','like','incompleta'),('lot_id','=',lot_id)])
no_lectures = clot_obj.search([('status','like',u'No t\xe9 lectures entrades'),('lot_id','=',lot_id)])
no_lectura_anterior = clot_obj.search([('status','like',u'No t\xe9 lectura anterior'),('status','not like',u'No t\xe9 lectures entrades'),('status','not like',u'incompleta'),('status','not like',u'volta de comptador'),('status','not like',u'Falta Lectura de tancament'),('status','not like',u'maxímetre'),('lot_id','=',lot_id)])
comptador_inactiu = clot_obj.search([('status','like','cap comptador actiu'),('lot_id','=',lot_id)])
baixa = clot_obj.search([('status','like','Falta Lectura de tancament amb data'),('lot_id','=',lot_id)])
no_lect_max = clot_obj.search([('status','like',u'No t\xe9 lectura de max\xedmetre'),('status','not like',u'No t\xe9 lectures entrades'),('status','not like',u'No t\xe9 lectura anterior'),('lot_id','=',lot_id)])
no_interval = clot_obj.search([('status','like',u'No t\xe9 cap interval a facturar'),('status','not like',u'No t\xe9 lectures entrades'),('status','not like',u'No t\xe9 lectura anterior'),('lot_id','=',lot_id)])
nou_comptador_una_lectura = clot_obj.search([('status','like','Possible primera lecutura'),('status','not like','volta de comptador'),('status','not like','incompleta'),('lot_id','=',lot_id)])
contractes_31 = clot_obj.search([('status','like','Falta P4,P5,P6'),('lot_id','=',lot_id)])



total_errors = set(sobreestimacions + maximetre + superior_limit + no_lectures + incompleta + comptador_inactiu + baixa + no_lectura_anterior + no_interval + no_lect_max)

#Resum del proces
print "\n" + "="*76
print "TOTAL %s" % total
print "    Finalitzats %s.(%d)" % (len(finalitzats), len(endarrerides(finalitzats)))
print "    Facturats %s" % facturat
print "    Per facturar %s" % per_facturar
print "    Oberts %s" % oberts
print "    Esborranys %s" % esborranys

print "\nERRORS %s (%d)" % (len(total_errors), len(endarrerides(list(total_errors))))
print "    Sobreestimacions %s (%d)" % (len(set(sobreestimacions)), len(endarrerides(sobreestimacions)))
print "    Exces del limit establert per SE %s (%d)" % (len(set(superior_limit)), len(endarrerides(superior_limit)))
print "    Excessos del 30 per cent. Maximetre %s (%d)" % (len(set(maximetre)), len(endarrerides(maximetre)))
print "    Lectura incompleta. Falten periodes %s (%d)" % (len(set(incompleta)), len(endarrerides(incompleta)))
print "    No té cap comptador actiu %s (%d)" % (len(set(comptador_inactiu)), len(endarrerides(comptador_inactiu)))
print "    Falta lectura de tancament %s (%d)" % (len(set(baixa)), len(endarrerides(baixa)))
print "    No té lectura anterior %s (%d)" % (len(set(no_lectura_anterior)), len(endarrerides(no_lectura_anterior)))
print "    No té lectura de maxímetre %s (%d)" % (len(set(no_lect_max)), len(endarrerides(no_lect_max)))
print "    No té interval a facturar %s (%d)" % (len(set(no_interval)), len(endarrerides(no_interval)))
print "    Primer lectura del nou comptador %s (%d)" % (len(set(nou_comptador_una_lectura)), len(endarrerides(nou_comptador_una_lectura)))
print "    Tarifa 3.1 no hi ha error  %s(%d)" % (len(set(contractes_31)), len(endarrerides(contractes_31)))
print " No te Lectures %s (%d)" % (len(set(no_lectures)), len(endarrerides(no_lectures)))
print " diff oberts i errors %s" % (oberts - len(total_errors))
print "="*76
