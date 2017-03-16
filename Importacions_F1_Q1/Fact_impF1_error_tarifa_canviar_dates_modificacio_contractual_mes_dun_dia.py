# -*- coding: utf-8 -*-
from ooop import OOOP
from datetime import datetime, timedelta
import configdb
 
O = OOOP(**configdb.ooop)

##Aquest script serveix per canviar dates de les modificacions contractuals que estiguin separades per més d'un dia!

#busquem la polissa que volguem amb el nom de la polissa
num_dies_a_canviar = int(raw_input("Dies a adelantar la data de la mod?"))
polissa = raw_input("polissa: ")

pol_id = O.GiscedataPolissa.search([('name','=',polissa)])

mod_contractuals = O.GiscedataPolissa.read(pol_id,['name','modcontractuals_ids'])

mod_actual = O.GiscedataPolissaModcontractual.get(mod_contractuals[0]['modcontractuals_ids'][0])
mod_antiga = O.GiscedataPolissaModcontractual.get(mod_contractuals[0]['modcontractuals_ids'][1])

data_final_incial = mod_antiga.data_final
data_final = datetime.strptime(mod_antiga.data_final,'%Y-%m-%d')
print "%s-->%s" % (mod_antiga.data_final,data_final)

data_inicial = mod_actual.data_inici
data_inici = datetime.strptime(mod_actual.data_inici,'%Y-%m-%d')
print "%s-->%s" % (mod_actual.data_inici,data_inici)

for a in range(num_dies_a_canviar):
    data_final = datetime.strftime(data_final + timedelta(1),'%Y-%m-%d')
    mod_antiga.write({'data_final': data_final})
    data_inici = datetime.strftime(data_inici + timedelta(1),'%Y-%m-%d')
    mod_actual.write({'data_inici': data_inici})

    mod_actual = O.GiscedataPolissaModcontractual.get(mod_contractuals[0]['modcontractuals_ids'][0])
    mod_antiga = O.GiscedataPolissaModcontractual.get(mod_contractuals[0]['modcontractuals_ids'][1])

    data_final_incial = mod_antiga.data_final
    data_final = datetime.strptime(mod_antiga.data_final,'%Y-%m-%d')

    data_inicial = mod_actual.data_inici
    data_inici = datetime.strptime(mod_actual.data_inici,'%Y-%m-%d')
    print "DATA FINAL: %s-->%s" % (mod_antiga.data_final,data_final)
    print "Data INICI: %s-->%s\n" % (mod_actual.data_inici,data_inici)