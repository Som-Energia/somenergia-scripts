from erppeek import Client
from datetime import datetime,timedelta
import configdb

O = Client(**configdb.erppeek)

pol_obj = O.GiscedataPolissa
sw_obj = O.GiscedataSwitching

def contractesTarifa(tarifa):
    pol_obj = O.GiscedataPolissa
    sw_obj = O.GiscedataSwitching

    pol_ids = pol_obj.search([('tarifa.name','=',tarifa)])
    pol_reads = pol_obj.read(pol_ids, ['cups'])
    pol_cups_ids = [a['cups'][0] for a in pol_reads if a['cups']]
    sol_pol = len(pol_ids)

    pol_inactived_ids = pol_obj.search([('cups','not in',pol_cups_ids),
                                ('tarifa.name','=',tarifa),
                                 ('active','=',False),
                                 ('data_alta','!=', False)])
    pol_inac = len(pol_inactived_ids)
 
    text_pol = 40*"=" + "\nContractes amb {tarifa}\n" + 40*"="
    text_pol += "\nSolicituds de contractes total: {sol_pol}"
    text_pol += "\nContractes de baixa : {pol_inac}\n"
    text_pol = text_pol.format(**locals())
    print text_pol

contractesTarifa('2.0A')
contractesTarifa('2.0DHA')
contractesTarifa('2.0DHS')
contractesTarifa('2.1A')
contractesTarifa('2.1DHA')
contractesTarifa('2.1DHS')
contractesTarifa('3.0A')
contractesTarifa('3.1A')
