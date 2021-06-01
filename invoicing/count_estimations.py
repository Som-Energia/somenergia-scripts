#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from consolemsg import step, success

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")

#Objectes
pol_obj = O.GiscedataPolissa

def calc_estimations():

    ## all
    all_pol_ids = pol_obj.search([])

    ## delayed ones
    delayed_pol_ids = pol_obj.search([
        ('facturacio_endarrerida','=',True),
        ])

    ## estimable
    estimable_ids = pol_obj.search([
        ('no_estimable','=',False),
        ('facturacio_potencia','=','icp'),
        ])

    ## not estimable
    f_not_estimable_ids = pol_obj.search([
        ('no_estimable','=',True)
        ])
    max_estimable_ids = pol_obj.search([
        ('facturacio_potencia','!=','icp'),
        ])
    not_estimable_ids = list(set(f_not_estimable_ids + max_estimable_ids))

    validation_esti_not_esti = "ok" if set(all_pol_ids) == set(estimable_ids + not_estimable_ids) else "error"

    ## estimable i endarrerida
    estimable_delayed_ids = list(set(estimable_ids) & set(delayed_pol_ids))

    ## estimable i no endarrerida
    estimable_not_delayed_ids = list(set(estimable_ids) - set(delayed_pol_ids))

    validation_esti_delayed_not_delayed = "ok" if set(estimable_ids) == set(estimable_delayed_ids + estimable_not_delayed_ids) else "error"

    ## no estimable i endarrerida
    not_estimable_delayed_ids = list(set(not_estimable_ids) & set(delayed_pol_ids))

    ## no estimable i no endarrerida
    not_estimable_not_delayed_ids = list(set(not_estimable_ids) - set(delayed_pol_ids))

    validation_not_esti_delayed_not_delayed = "ok" if set(not_estimable_ids) == set(not_estimable_delayed_ids + not_estimable_not_delayed_ids) else "error"

    success("--------------------------")
    success(" RESULTAT ESTAT ESTIMACIO")
    success("--------------------------")
    success("polisses totals ........................... {}",len(all_pol_ids))
    success("polisses estimables ....................... {}",len(estimable_ids))
    success("polisses no estimables .................... {}",len(not_estimable_ids))
    success("tot encaixa ? ............................. {}",validation_esti_not_esti)
    success("")
    success(" - percentatge p. estimables .............. {:.2f} %",(len(estimable_ids) * 100.0) / len(all_pol_ids))
    success(" - percentatge p. no estimables ........... {:.2f} %",(len(not_estimable_ids) * 100.0) / len(all_pol_ids))
    success("")
    success("SEGMENTACIO ESTIMABLES PER ENDARRERIDES")
    success("---------------------------------------")
    success("polisses endarrerides ..................... {}",len(delayed_pol_ids))
    success("polisses estimables ....................... {}",len(estimable_ids))
    success("polisses estimables i endarrerides ........ {}",len(estimable_delayed_ids))
    success("polisses estimables i no endarrerides ..... {}",len(estimable_not_delayed_ids))
    success("tot encaixa ? ............................. {}",validation_esti_delayed_not_delayed)
    success("")
    success("percentatge sobre totes")
    success(" - estimables i endarrerides .............. {:.2f} %",(len(estimable_delayed_ids) * 100.0) / len(all_pol_ids))
    success(" - estimables i no endarrerides ........... {:.2f} %",(len(estimable_not_delayed_ids) * 100.0) / len(all_pol_ids))
    success("")
    success("percentatge sobre estimables")
    success(" - estimables i endarrerides .............. {:.2f} %",(len(estimable_delayed_ids) * 100.0) / (len(estimable_ids) or 1.0))
    success(" - estimables i no endarrerides ........... {:.2f} %",(len(estimable_not_delayed_ids) * 100.0) / (len(estimable_ids) or 1.0))
    success("")
    success("SEGMENTACIO NO ESTIMABLES PER ENDARRERIDES")
    success("------------------------------------------")
    success("polisses endarrerides ..................... {}",len(delayed_pol_ids))
    success("polisses no estimables .................... {}",len(not_estimable_ids))
    success("polisses no estimables i endarrerides ..... {}",len(not_estimable_delayed_ids))
    success("polisses no estimables i no endarrerides .. {}",len(not_estimable_not_delayed_ids))
    success("tot encaixa ? ............................. {}",validation_not_esti_delayed_not_delayed)
    success("")
    success("percentatge sobre totes")
    success(" - no estimables i endarrerides ........... {:.2f} %",(len(not_estimable_delayed_ids) * 100.0) / len(all_pol_ids))
    success(" - no estimables i no endarrerides ........ {:.2f} %",(len(not_estimable_not_delayed_ids) * 100.0) / len(all_pol_ids))
    success("")
    success("percentatge sobre no estimables")
    success(" - no estimables i endarrerides ........... {:.2f} %",(len(not_estimable_delayed_ids) * 100.0) / len(not_estimable_ids))
    success(" - no estimables i no endarrerides ........ {:.2f} %",(len(not_estimable_not_delayed_ids) * 100.0) / len(not_estimable_ids))
    success("")
    success("BONUS:")
    success("percentatge d'endarrerides ................ {:.2f} %",(len(delayed_pol_ids) * 100.0) / len(all_pol_ids))
    success("")
    success("Nota:")
    success("polissa estimable => polissa que pot estimar lectures")
    success("polissa no estimable => polissa que NO pot estimar lectures (check no estimable o maximetre)")


if __name__=='__main__':
    res = calc_estimations()

# vim: et ts=4 sw=4
