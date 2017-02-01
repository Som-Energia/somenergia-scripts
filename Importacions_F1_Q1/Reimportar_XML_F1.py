# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

cups_name = ''
vals_search = [('state','=','erroni'),('cups_id','=','cups_name')]

lin_obj = O.GiscedataFacturacioImportacioLinia
erronis_id = lin_obj.search(vals_search)

#comptadors
count=0
total=len(erronis_id)

print "Hi ha %d amb importacions erronies inicials" % total

#Incialitzem comptadors
imp_sense_canvis = []
imp_amb_canvi = []

for linia_id in erronis_id:
    info_inicial = lin_obj.read(linia_id,['info'])
    linia_nova_id = lin_obj.process_line(linia_id)
    info_nova = lin_obj.read(linia_nova_id,['info'])
    count+=1
    if info_inicial == info_nova:
        print "informacio igual: %s" % info_inicial
        imp_sense_canvis.append(linia_id)
    else:
        print "Missatge Inicial: %s \n Missatge Final: %s" % (info_inicial,info_nova)
        imp_amb_canvi.append(imp_id)
    print "%d/%d"%(count,total)
        
        
erronis_finals_ids = lin_obj.search(vals_search)  

erronis_finals = len(erronis_finals_id)
print "Hi havia %d amb importacions erronies inicials, sense el missatge 'Ja existeix una factura'" % total
print "Desrpés del script, hi ha %d amb importacions erronies, sense el missatge 'Ja existeix una factura...' " % erronis_finals
print "S'han importat bé %d arxius xml" % (total-erronis_finals)
