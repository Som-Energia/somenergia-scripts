# -*- coding: cp1252 -*-
from ooop import OOOP
from datetime import datetime, timedelta
import configdb

O = OOOP(**configdb.ooop)

#Objectes
wiz_obj = O.GiscedataFacturacioSwitchingWizard
imp_obj = O.GiscedataFacturacioImportacioLinia
pol_obj = O.GiscedataPolissa
lect_pool_obj = O.GiscedataLecturesPotenciaPool

imp_amb_canvi = []
imp_sense_canvis = []


##-- Busquem les polisses que tinguin el missatge d'error lectures de maximetre--##
erronis_ids = imp_obj.search([('state','=','erroni'),('info','like','Tipus: M')])
cups_erronis = imp_obj.read(erronis_ids,['cups_id'])
cups = []
for cups_id in cups_erronis:
    if cups_id['cups_id']:
        cups.append(cups_id['cups_id'][1])   
pol_ids = pol_obj.search([('cups.name','in',cups)])
pols_reads = pol_obj.read(pol_ids,['comptador','cups','name','potencia'])


#Busquem lectures per polissa
for pol_read in pols_reads:
    print "Polissa: %s" % pol_read['name']
    lect_ids = lect_pool_obj.search([('comptador','=',pol_read['comptador']),('lectura','>=',pol_read['potencia']*10)])
    lect_reads = lect_pool_obj.read(lect_ids,['lectura'])

    for lect_read in lect_reads:
        lectura_bona = lect_read['lectura']/1000
        print "%s --> %s" % (lect_read['lectura'],lectura_bona)
        lect_pool_obj.write(lect_read['id'],{'lectura':lectura_bona})

    if lect_reads:
        ##-- Re-importem el F1 --##
        imp_id = imp_obj.search([('state','=','erroni'),('cups_id','=',pol_read['cups'][1]),('info','like','Tipus: M')])
        imp_ = imp_obj.read(imp_id,['info','conte_factures'])
        ##### Pot ser que hi hagi més d'una factura encallada, PENSAR EN QUIN ORDRE LES VOLEM ARREGLAR!!
        for imp in imp_:
            info_inicial = imp['info']
            ctx = {'active_id':imp['id'], 'fitxer_xml': True}
            wz_id = wiz_obj.create({}, ctx)
            wiz = wiz_obj.get(wz_id)
            wiz.action_importar_f1(ctx)
        
            imp_nou = O.GiscedataFacturacioImportacioLinia.read(imp['id'],['info','conte_factures'])
            if imp_nou['conte_factures']:
                print "Factura importada correctament! Polissa: %s" % pol_read['name']
                imp_amb_canvi.append(pol_read['cups'])
            else:
                if info_inicial == imp_nou['info']:
                    print "Informació igual."
                    imp_sense_canvis.append(pol_read['cups'])
                else:
                    print "Missatges diferents: Info final  : %s." % imp_nou['info']
