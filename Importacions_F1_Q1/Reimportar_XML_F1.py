# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)
imp_cups = True
if imp_cups:
    vals_search = [('state','=','erroni'),('cups_id','=','cups_name')]


erronis_id = O.GiscedataFacturacioImportacioLinia.search(vals_search)
wiz_obj = O.GiscedataFacturacioSwitchingWizard

#comptadors
count=0
total=len(erronis_id)

print "Hi ha %d amb importacions erronies inicials" % total

#Incialitzem comptadors
imp_sense_canvis = []
imp_amb_canvi = []

for imp_id in erronis_id:
    imp = O.GiscedataFacturacioImportacioLinia.read(imp_id,['info'])
    info_inicial = imp['info']
    ctx = {'active_id':imp_id, 'fitxer_xml': True}
    wz_id = wiz_obj.create({}, ctx)
    wiz = wiz_obj.get(wz_id)
    wiz.action_importar_f1(ctx)
    imp = O.GiscedataFacturacioImportacioLinia.read(imp_id,['info'])
    count+=1
    if info_inicial == imp['info']:
        print "informacio igual: %s" % info_inicial
        imp_sense_canvis.append(imp_id)
    else:
        print "Missatge Inicial: %s \n Missatge Final: %s" % (info_inicial, imp['info'])
        imp_amb_canvi.append(imp_id)
    print "%d/%d"%(count,total)
        
        
erronis_finals_id = O.GiscedataFacturacioImportacioLinia.search(vals_search)  

erronis_finals = len(erronis_finals_id)
print "Hi havia %d amb importacions erronies inicials, sense el missatge 'Ja existeix una factura'" % total
print "Desrpés del script, hi ha %d amb importacions erronies, sense el missatge 'Ja existeix una factura...' " % erronis_finals
print "S'han importat bé %d arxius xml" % (total-erronis_finals)
