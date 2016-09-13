# -*- coding: utf-8 -*-
from ooop import OOOP
from datetime import datetime, timedelta
import configdb
import argparse

O = OOOP(**configdb.ooop)

#Objectes
wiz_obj = O.GiscedataFacturacioSwitchingWizard
imp_obj = O.GiscedataFacturacioImportacioLinia
pol_obj = O.GiscedataPolissa
mod_obj = O.GiscedataPolissaModcontractual

##-- Busquem les polisses que tinguin el missatge de tarifa incoherent --##
now = datetime.now()
start_date = (now - timedelta(days=14)).strftime('%Y-%m-%d')

erronis_ids = imp_obj.search([('state','=','erroni'),('info','like',': La tarifa ('),('data_carrega','>', start_date)])
cups_erronis = imp_obj.read(erronis_ids,['cups_id','distribuidora'])
cups = []
for cups_id in cups_erronis:
    if cups_id['cups_id']:
        cups.append(cups_id['cups_id'][1])   
pol_ids = pol_obj.search([('cups.name','in',cups)])

#Comptadors i taules
imp_sense_canvis = []
imp_amb_canvi = []
errors = []
total_erronis = len(erronis_ids)
total= len(pol_ids)
count = 0

def reimportar_F1(cups_id):
    imp_obj = O.GiscedataFacturacioImportacioLinia
    wiz_obj = O.GiscedataFacturacioSwitchingWizard
    
    vals_search = [('state','=','erroni'),('cups_id','=',cups_id)]
    imp_ids = imp_obj.search(vals_search)
    for imp_id in imp_ids:
        imp_read = O.GiscedataFacturacioImportacioLinia.read(imp_id,['info'])
        ctx = {'active_id':imp_id, 'fitxer_xml': True}
        wz_id = wiz_obj.create({}, ctx)
        wiz = wiz_obj.get(wz_id)
        wiz.action_importar_f1(ctx)
        imp_new_id = O.GiscedataFacturacioImportacioLinia.read(imp_id,['info'])
        if imp_read['info'] == imp_new_id['info']:
            return False
        else:
            return False


# Pot ser que una polissa tingui mes d'una factura per arreglar, d'aixo la diferencia entres els dos numeros.
print " ######### \n De les %s importacions erronies hem trobat %s polisses per arreglar\n ######### \n" % (total_erronis, total)
print "                                        %d/%d" % (0,total)
for pol_id in pol_ids:
    try:
        mod_contractuals = pol_obj.read(pol_id,['name','modcontractuals_ids'])
        if len(mod_contractuals['modcontractuals_ids'])>1:
            for a in [-1,1]:
                ##--Busquem i canviem les dates d'inici i final de les modificacions--##
                mod_actual = mod_obj.get(mod_contractuals['modcontractuals_ids'][0])
                mod_antiga = mod_obj.get(mod_contractuals['modcontractuals_ids'][1])
                print "--> Contracte amb CUPS:                   %s" % mod_actual.cups.name
                print "--> Contracte número de polissa:           %s" % mod_contractuals['name']
                
                data_final_inicial = mod_antiga.data_final
                data_final = datetime.strptime(mod_antiga.data_final,'%Y-%m-%d')
                data_final = datetime.strftime(data_final + timedelta(a),'%Y-%m-%d')
                print "%s-->%s" % (mod_antiga.data_final,data_final)
                mod_antiga.write({'data_final': data_final})
                
                data_inicial = mod_actual.data_inici
                data_inici = datetime.strptime(mod_actual.data_inici,'%Y-%m-%d')
                data_inici = datetime.strftime(data_inici + timedelta(a),'%Y-%m-%d')
                print "%s-->%s" % (mod_actual.data_inici,data_inici)
                mod_actual.write({'data_inici': data_inici})
                
        
                
                ##-- Re-importem el F1 --##
                imp_id = imp_obj.search([('state','=','erroni'),('cups_id.name','=',mod_actual.cups.name),('info','like',': La tarifa (')])
                imp_ = imp_obj.read(imp_id,['info','conte_factures'])
                ##### Pot ser que hi hagi mes d'una factura encallada, PENSAR EN QUIN ORDRE LES VOLEM ARREGLAR!!
                if len(imp_id)>1:
                    print "te mes d'uan factura encallada"
                mod_data=False
                for imp in imp_:
                    info_inicial = imp['info']
                    ctx = {'active_id':imp['id'], 'fitxer_xml': True}
                    wz_id = wiz_obj.create({}, ctx)
                    wiz = wiz_obj.get(wz_id)
                    wiz.action_importar_f1(ctx)
                
                    imp_nou = O.GiscedataFacturacioImportacioLinia.read(imp['id'],['info','conte_factures'])
                    if imp_nou['conte_factures']:
                        print "Factura importada correctament! Polissa: %s" % mod_contractuals['name']
                        imp_amb_canvi.append(mod_contractuals['name'])
                    else:
                        if info_inicial == imp_nou['info']:
                            print "Informacio igual. Tornem a posar les dates de les modificacions tal i com estaven"
                            imp_sense_canvis.append(imp['id'])
                        else:
                            print "Missatges diferents: Info final  : %s. Tornem a posar les dates de les modificacions tal i com estaven" % imp_nou['info']
                        ## -- tornem a posar les dates com estaven inicialment --##
                        mod_antiga.write({'data_final': data_final_inicial})
                        mod_actual.write({'data_inici': data_inicial})         
        else: 
            print "La polissa %s te %s modficacions contractuals, no hem fet cap canvi" % (mod_contractuals['name'],len(mod_contractuals['modcontractuals_ids']))
            ### si el num de modificacions es igual a 1, cnaviar tarifa i reimportar, sino funciona, tornar tot com estava.
        count+=1
        print "                                        %d/%d"%(count,total)
    except Exception, e:
        errors.append({pol_id:e})
        print e
        
erronis_finals_id = imp_obj.search([('state','=','erroni'),('info','like',': La tarifa (')])
erronis_finals = len(erronis_finals_id)
total_imp = len(imp_amb_canvi)

##-- Imprimim per pantalla els esultats dels script --##
print "\nHi havia %d amb importacions erronies per intentar arreglar del total (%s) de les importacions erronies" % (total, total_erronis)
print "Despres del script, hi ha %d importacions erronies amb missatge 'tarifa incoherent'" % erronis_finals
print "S'han importat be %d arxius xml" % (total_imp)
print "Errors: {}".format(len(errors))
