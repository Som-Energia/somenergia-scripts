#!/usr/bin/python
# -*- coding: utf-8 -*-
from erppeek import Client
from datetime import datetime,timedelta
import configdb

O = Client(**configdb.erppeek)

#facturacio impagats 3.0A  i normals

def endarrerides(clot_ids):
    pol_obj = O.GiscedataPolissa
    clot_obj = O.GiscedataFacturacioContracte_lot
    pol_ids = [a['polissa_id'][0] for a in clot_obj.read(clot_ids,['polissa_id'])]
    endarrerides = pol_obj.search([('facturacio_endarrerida','=',True),
                                    ('id','in',pol_ids)])
    return endarrerides

def polisses_en_lots(lot_id_actual):
    pol_obj = O.GiscedataPolissa
    print "- Polisses en els lots a cada lot"
    lot_ids = [lot_id_actual + a -4 for a in range(10)]
    for lot_id in lot_ids:
        pol_lot = len(pol_obj.search([('lot_facturacio','=',lot_id),
                                        ('state','=','activa')]))
        if pol_lot:
            lot_name = lot_obj.read(lot_id,['name'])['name']
            print "    - Lot: {lot_name} --> {pol_lot}".format(**locals())
    
def polisses_sense_lot():
    pol_obj = O.GiscedataPolissa
    pol_sense_lot = len(pol_obj.search([('lot_facturacio','=',False),
                                    ('state','=','activa')]))

    print "- Polisses sense lot: {pol_sense_lot}".format(**locals())
    

def num_endarrerides():
    pol_obj = O.GiscedataPolissa
    num = len(pol_obj.search([('facturacio_endarrerida','=',True)]))
    num_3 = len(pol_obj.search([('facturacio_endarrerida','=',True),
                                ('tarifa','=','3.0A')]))
    print " - Endarrides total: {num}".format(**locals())
    print "       - 3.0A: {num_3}".format(**locals())

# Polisses de baixa amb data != a data ultima lectura
sql_query = """select name,
	data_ultima_lectura,
	data_baixa,
	(data_baixa - data_ultima_lectura)
from giscedata_polissa
where not active
	and not(data_ultima_lectura = data_baixa)
	and (data_baixa - data_ultima_lectura) != 1
	and data_baixa >= '2015-07-01'
/*** Treure els casos amb la categoria de baixa per impagament ***/

order by data_baixa desc"""

# Factures en esborrany que no siguin d'avui
def factures_abandonades():
    fact_obj = a
# Factures abonadores que no siguin d'avui

# Numero de Reclamacions

# Quadre de control del Validacio


#Objectes
def validacio_facturacio(lot_id):
    try:
        clot_obj = O.GiscedataFacturacioContracte_lot
    
        total = clot_obj.search([('lot_id','=',lot_id)])
        finalitzats = clot_obj.search([('state','like','finalitzat'),
                                        ('lot_id','=',lot_id)])
        facturat = clot_obj.search([('state','like','facturat'),
                                    ('lot_id','=',lot_id)])
        per_facturar = clot_obj.search([('state','like','facturar'),
                                        ('lot_id','=',lot_id)])
        oberts = clot_obj.search([('state','like','obert'),
                                ('lot_id','=',lot_id)])
        esborranys = clot_obj.search([('state','like','facturat'),
                                    ('lot_id','=',lot_id)])
        
        
        
        
        sobreestimacions = clot_obj.search([('status','like','volta de comptador'),
                                            ('status','not like','incompleta'),
                                            ('lot_id','=',lot_id)])
        maximetre= clot_obj.search([('status','like','maxímetre '),
                                    ('lot_id','=',lot_id)])
        superior_limit = clot_obj.search([('status','not like','volta de comptador'),
                                            ('status','like','superior al lími'),
                                            ('status','not like','incompleta'),
                                            ('lot_id','=',lot_id)])
        incompleta = clot_obj.search([('status','like','incompleta'),
                                        ('lot_id','=',lot_id)])
        no_lectures = clot_obj.search([('status','like',u'No t\xe9 lectures entrades'),
                                        ('lot_id','=',lot_id)])
        no_lectura_anterior = clot_obj.search([('status','like',u'No t\xe9 lectura anterior'),
                                    ('status','not like',u'No t\xe9 lectures entrades'),
                                    ('status','not like',u'incompleta'),
                                    ('status','not like',u'volta de comptador'),
                                    ('status','not like',u'Falta Lectura de tancament'),
                                    ('status','not like',u'maxímetre'),
                                    ('lot_id','=',lot_id)])
        comptador_inactiu = clot_obj.search([('status','like','cap comptador actiu'),
                                            ('lot_id','=',lot_id)])
        baixa = clot_obj.search([('status','like','Falta Lectura de tancament amb data'),
                                ('lot_id','=',lot_id)])
        no_lect_max = clot_obj.search([('status','like',u'No t\xe9 lectura de max\xedmetre'),
                                        ('status','not like',u'No t\xe9 lectures entrades'),
                                        ('status','not like',u'No t\xe9 lectura anterior'),
                                        ('lot_id','=',lot_id)])
        no_interval = clot_obj.search([('status','like',u'No t\xe9 cap interval a facturar'),
                                    ('status','not like',u'No t\xe9 lectures entrades'),
                                    ('status','not like',u'No t\xe9 lectura anterior'),
                                    ('lot_id','=',lot_id)])
        nou_comptador_una_lectura = clot_obj.search([('status','like','Possible primera lecutura'),
                                                ('status','not like','volta de comptador'),
                                                ('status','not like','incompleta'),
                                                ('lot_id','=',lot_id)])
        contractes_31 = clot_obj.search([('status','like','Falta P4,P5,P6'),
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
    
    except Exception, e:
        print e
        
# Quadre de control de Importacio F1
def importacions_f1(data_carrega):
    imp_obj = O.GiscedataFacturacioImportacioLinia
    
    vals_search = [('state','=','erroni'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    erronis = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','Ja existeix una factura'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_ja = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','Divergència'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_div = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','La tarifa ('),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_tar = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','trobat la factura de referència amb número'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_ref = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','Error introduint lectures en data inicial'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_dat_in = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','Error introduint lectures en data fi'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_dat_fi = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','identificar tots els períodes'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_per = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','trobat el CUPS'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_cups = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','assignat el comptador'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_comp = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','lissa vinculada al cups'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_pol_cups = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','Empresa emisora no correspon'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_emp = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','Error no existeix cap modificació'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_mod = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','float division'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_float = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','XML erroni'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_xml = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','Document invàlid'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_invalid = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like','child'),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_child = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like',"No s'ha pogut identificar tots els períodes de reactiva per facturar"),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_reactiva = len(erronis_ids)
    
    vals_search = [('state','=','erroni'),('info','like',"XML no es correspon al tipus F1"),('data_carrega','>',data_carrega)]
    erronis_ids = imp_obj.search(vals_search)
    err_no_F1 = len(erronis_ids)
    
    
    print "ERRORS DE IMPORTACIONS"
    print "TOTAL: %d" % erronis
    print " --> Divergències: %d" % err_div
    print " --> Factura de Referència: %d" % err_ref
    print " --> Data Inicial Erronia: %d" % err_dat_in
    print " --> Data final Erronia: %d" % err_dat_fi
    print " --> Tarifa errònia: %d" % err_tar
    print " --> Error Periodes: %d" % err_per
    print " --> Sense CUPS : %d" % err_cups 
    print " --> Comptador diferent de la pòlissa: %d" % err_comp
    print " --> No hi ha cap polissa vincula al cups: %d" % err_pol_cups 
    print " --> Empresa emisora no correspon: %d" % err_emp
    print " --> No existeix cap modificació contractual: %d" % err_mod
    print " --> Float division by zero: %d" % err_float
    print " --> XML_erroni: %d" % err_xml
    print " --> Document invàlid: %d" % err_invalid
    print " --> No such child: %d" % err_child
    print " --> Problemes amb la reactiva: %d" % err_child
    print "--> Ja existeix una factura..: %d" % err_ja
    print "--> XML no es correspon al tipus F1: %d" % err_no_F1
    
    desajust = erronis - err_no_F1 - err_per - err_dat_fi - err_dat_in - err_ref - err_tar - err_div -err_comp - err_pol_cups -err_emp -err_reactiva - err_mod - err_float - err_xml -err_invalid -err_cups - err_child -err_ja
    
    print "\n SENSE IDENTIFICAR --> %d" % desajust


lot_obj = O.GiscedataFacturacioLot

lot_id_actual = lot_obj.search([('state','=','obert')])[0]

#main
print "LOTS" + "_"*76
polisses_en_lots(lot_id_actual)
polisses_sense_lot()

print "\nEndarrerides" + "_"*76
num_endarrerides()

print "\nFactures" + "_"*76

print "\nReclamacions" + "_"*76



