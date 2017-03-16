# -*- coding: utf-8 -*-
from ooop import OOOP
from datetime import datetime, timedelta
import configdb
import argparse

O = OOOP(**configdb.ooop)

#Objectes
lin_obj = O.GiscedataFacturacioImportacioLinia
pol_obj = O.GiscedataPolissa
mod_obj = O.GiscedataPolissaModcontractual

##-- Busquem les polisses que tinguin el missatge de tarifa incoherent --##
now = datetime.now()
start_date = (now - timedelta(days=14)).strftime('%Y-%m-%d')

erronis_ids = lin_obj.search([('state','=','erroni'),('info','like',': La tarifa ('),('data_carrega','>', start_date)])
cups_erronis = lin_obj.read(erronis_ids,['cups_id','distribuidora'])
cups = []
for cups_id in cups_erronis:
    if cups_id['cups_id']:
        cups.append(cups_id['cups_id'][1])   
pol_ids = pol_obj.search([('cups.name','in',cups)])

#Comptadors i taules
lin_sense_canvis = []
lin_amb_canvi = []
errors = []
total_erronis = len(erronis_ids)
total= len(pol_ids)
count = 0

def reimportar_ok(linia_id):
    import time
    lin_obj = O.GiscedataFacturacioImportacioLinia
    info_inicial = lin_obj.read([linia_id],['info'])[0]['info']
    lin_obj.process_line(linia_id)
    time.sleep(15)
    lin_read = lin_obj.read([linia_id],['info','conte_factures'])
    info_nova = lin_read[0]['info']
    conte_factures = lin_read[0]['conte_factures']
    value = {'mateix_missatge':False,'ok':False}
    if lin_read[0]['conte_factures']:
        value['ok'] = True
    if info_inicial == info_nova:
        #print "informacio igual: %s" % info_inicial
        print "Mateix missatge"
        value['mateix_missatge']=True
    else:
        #print "Missatge Inicial: %s \n Missatge Final: %s" % (info_inicial,info_nova)
        print "S'ha actualitzat el missatge"
    return value

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
                lin_ids = lin_obj.search([('state','=','erroni'),('cups_id.name','=',mod_actual.cups.name),('info','like',': La tarifa (')])
                ##### Pot ser que hi hagi mes d'una factura encallada, PENSAR EN QUIN ORDRE LES VOLEM ARREGLAR!!
                if len(lin_ids)>1:
                    print "te mes d'una factura encallada"
                mod_data=False
                for lin_id in lin_ids:
                    reimportacio = reimportar_ok(lin_id)
                    if reimportacio['ok']:
                        print "Factura importada correctament! Polissa: %s" % mod_contractuals['name']
                        lin_amb_canvi.append(mod_contractuals['name'])
                        break
                    if reimportacio['mateix_missatge']:
                        print "Informacio igual. Tornem a posar les dates de les modificacions tal i com estaven"
                        lin_sense_canvis.append(lin_id)
                    else:
                        print "Missatges diferents: Info final  : %s. Tornem a posar les dates de les modificacions tal i com estaven" % lin_nou['info']
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
        
erronis_finals_id = lin_obj.search([('state','=','erroni'),('info','like',': La tarifa (')])
erronis_finals = len(erronis_finals_id)
total_lin = len(lin_amb_canvi)

##-- Imprimim per pantalla els esultats dels script --##
print "\nHi havia %d amb importacions erronies per intentar arreglar del total (%s) de les importacions erronies" % (total, total_erronis)
print "Despres del script, hi ha %d importacions erronies amb missatge 'tarifa incoherent'" % erronis_finals
print "S'han importat be %d arxius xml" % (total_lin)
print "Errors: {}".format(len(errors))
