#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

def endarrerides(clot_ids):
    pol_ids = [a['polissa_id'][0] for a in clot_obj.read(clot_ids,['polissa_id'])]
    endarrerides = pol_obj.search([('facturacio_endarrerida','=',True),('id','in',pol_ids)])
    return endarrerides

#Objectes
clot_obj = O.GiscedataFacturacioContracte_lot
lot_obj = O.GiscedataFacturacioLot
pol_obj = O.GiscedataPolissa

lot_id = lot_obj.search([('state','=','obert')])

total = clot_obj.search([('lot_id','=',lot_id)])
finalitzats = clot_obj.search([('state','like','finalitzat'),
                                ('lot_id','=',lot_id)])
facturat = clot_obj.search([('state','like','facturat'),
                            ('lot_id','=',lot_id)])
per_facturar = clot_obj.search([('state','like','facturar'),
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



total_errors = set(sobreestimacions + maximetre + superior_limit + no_lectures + incompleta + comptador_inactiu + baixa + no_lectura_anterior + no_interval + no_lect_max)

#Resum del proces
print "\n" + "="*76
print "TOTAL {}".format(len(total))
print "    Finalitzats {}. Endarrerits {}".format(len(finalitzats), len(endarrerides(finalitzats)))
print "    Facturats {}".format(len(facturat))
print "    Per facturar {}".format(len(per_facturar))
print "    Oberts {}".format(len(oberts))
print "    Esborranys {}".format(len(esborranys))
print "    A punt per facturar {}".format(len(apunt))

print "\nERRORS {}. Endarrerits {}".format(len(total_errors), len(endarrerides(list(total_errors))))
print "    Sobreestimacions {}. Endarrerits {}".format(len(set(sobreestimacions)), len(endarrerides(sobreestimacions)))
print "    Lectura incompleta. Falten periodes {}. Endarrerits {}".format(len(set(incompleta)), len(endarrerides(incompleta)))
print "    Falta lectura de tancament {}. Endarrerits {}".format(len(set(baixa)), len(endarrerides(baixa)))
print "    No té cap comptador actiu {}. Endarrerits {}".format(len(set(comptador_inactiu)), len(endarrerides(comptador_inactiu)))
print "    No té lectura anterior {}. Endarrerits {}".format(len(set(no_lectura_anterior)), len(endarrerides(no_lectura_anterior)))
print "    No té lectura de maxímetre {}. Endarrerits {}. (MARTA)".format(len(set(no_lect_max)), len(endarrerides(no_lect_max)))
print "    Excessos del 30 per cent. Maximetre {}. Endarrerits {}. (MANEL)".format(len(set(maximetre)), len(endarrerides(maximetre)))
print '    Tarifa 3.1 no hi ha error {}. Endarrerits {}'.format(len(set(contractes_31)), len(endarrerides(contractes_31)))
print "    No té interval a facturar {}. Endarrerits {}".format(len(set(no_interval)), len(endarrerides(no_interval)))
print "    Primer lectura del nou comptador {}. Endarrerits {}".format(len(set(nou_comptador_una_lectura)), len(endarrerides(nou_comptador_una_lectura)))
print "    Exces del limit establert per SE {}. Endarrerits {}".format(len(set(superior_limit)), len(endarrerides(superior_limit)))
print " No te Lectures {}. Endarrerits {}".format(len(set(no_lectures)), len(endarrerides(no_lectures)))
print " diferencia oberts i errors {}".format(len(oberts) - len(total_errors))
print "="*76
