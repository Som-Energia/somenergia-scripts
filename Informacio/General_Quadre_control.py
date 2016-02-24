# -*- coding: utf-8 -*-
#Quadre de control
from ooop import OOOP
from datetime import datetime
import configdb
from sys import argv

O = OOOP(**configdb.ooop)

pol_obj = O.GiscedataPolissa
sw_obj = O.GiscedataSwitching

data = str(input("Escriu la data fins que volem tenir la informació (inclosa) amb format (amb les cometes!) 'aaaa-mm-dd' :  "))
if not(data):
    data = datetime.today().strftime('%Y-%m-%d')

data_search = ('data_firma_contracte','<=',data)

solicituts_erronies = len(pol_obj.search([('data_firma_contracte','=',False)]))
solicituts = len(pol_obj.search([data_search]))
solicituts_30A = len(pol_obj.search([('tarifa','=','3.0A'),data_search]))
activats_30A = len(pol_obj.search([('tarifa','=','3.0A'),
                                    ('state','=','activa'),
                                    data_search]))
factures_endarrerides = len(pol_obj.search([('facturacio_endarrerida','=',True),
                                            data_search]))
baixes = len(pol_obj.search([('active','=',0),
                    ('data_baixa','<=',data)]))
activats = len(pol_obj.search([('data_alta','<=',data),
                            ('state','=','activa')]))
acceptats = len(sw_obj.search([('proces_id.name','in',['C1','C2']),
                               ('state','=','open'),
                               ('rebuig','=',False),
                               ('step_id.name','=','02')]))
activats_oberts = len(sw_obj.search([('proces_id.name','in',['C1','C2']),
                                    ('state','=','open'),
                                    ('step_id.name','in',['05','07'])]))
sol_acceptades = activats + acceptats + activats_oberts
Sol_problematiques = solicituts-sol_acceptades

print "Solicituds erronies {solicituts_erronies}".format(**locals())
print "Solicituts: {solicituts}".format(**locals())
print "Solicituts tarifa 3.0A: {solicituts_30A}".format(**locals())
print "Solicituts Activats 3.0A: {activats_30A}".format(**locals())
print "Solicituts Contractes donats de baixa: {baixes}".format(**locals())
print "Solicituts Factures endaderrides: {factures_endarrerides}".format(**locals())
print "Solicituts Solicituds problematiques: {Sol_problematiques}".format(**locals())
print "Solicituts Contractes aceptats: {sol_acceptades}".format(**locals())
print "Solicituts Contractes activats: {activats}".format(**locals())
