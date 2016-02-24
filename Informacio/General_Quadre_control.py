# -*- coding: utf-8 -*-
#Quadre de control
from ooop import OOOP
from datetime import datetime
import configdb

O = OOOP(**configdb.ooop)

pol_obj = O.GiscedataPolissa

data = str(input("Escriu la data fins que volem tenir la informació (inclosa) amb format (amb les cometes!) 'aaaa-mm-dd' :  "))
if not(data):
    data = datetime.today().strftime('%Y-%m-%d')

solicituts_erronies = len(pol_obj.search([('data_firma_contracte','=',False)]))

solicituts = len(pol_obj.search([('data_firma_contracte','<=',data)]))

solicituts_30A = len(pol_obj.search([('tarifa','=','3.0A'),('data_firma_contracte','<=',data)]))
activats_30A = len(pol_obj.search([('tarifa','=','3.0A'),('data_firma_contracte','<=',data),('state','=','activa')]))

factures_endarrerides = len(pol_obj.search([('facturacio_endarrerida','=',True),]))
baixes = len(pol_obj.search([('active','=',0),('data_baixa','<=',data)]))

activats = len(pol_obj.search([('data_alta','<=',data),('state','=','activa')]))


acceptats = len(O.GiscedataSwitching.search([('proces_id.name','in',['C1','C2']),('state','=','open'),('rebuig','=',False),('step_id.name','=','02')]))

activats_oberts = len(O.GiscedataSwitching.search([('proces_id.name','in',['C1','C2']),('state','=','open'),('step_id.name','in',['05','07'])]))

sol_acceptades = activats + acceptats + activats_oberts

Sol_problematiques = solicituts-sol_acceptades

print "Solicituds erronies %d\n Solicituts: %d\n Solicituts tarifa 3.0A: %d\n Activats 3.0A %d\n Contractes donats de baixa: %d \n Factures endaderrides: %d \n Solicituds problematiques: %d \n Contractes aceptats: %d \n Contractes activats: %d" % (solicituts_erronies, solicituts, solicituts_30A,activats_30A,baixes, factures_endarrerides,Sol_problematiques, sol_acceptades, activats)
