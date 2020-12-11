#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from consolemsg import step, success, error, warn, color, printStdError
from datetime import datetime, timedelta
from yamlns import namespace as ns

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

pol_obj = O.GiscedataPolissa

versio = "v2.1"
missatge = "Desactivem el sistema d'estimació ja que té maximetre "

doit = False
success('')
if doit:
    success("Es faran canvis a les polisses (doit=True)")
else:
    success("No es faran canvis a les polisses (doit=False)")

pol_ids = pol_obj.search([
    ('no_estimable','=',False), # estimable
    ('facturacio_potencia','=','max'), # maximeter
    ]) 
 
errors = []

totals = len(pol_ids)
for counter,pol_id in enumerate(pol_ids):

    polissa = ns(pol_obj.read(pol_id,[
        "name",
        "no_estimable",
        "observacions",
        "observacions_estimacio",
        ]))
    step("{}/{} polissa {}".format(counter+1,totals,polissa.name))

    header = "[{}] ".format(str(datetime.today())[:19])

    if polissa.observacions:
        polissa.observacions = polissa.observacions.encode("utf-8")
    changes = {
        "observacions": header + missatge + "\n\n"+ (polissa.observacions or ""),
        "observacions_estimacio": header + missatge,
        "no_estimable":True,
    }
    if doit:
        try:
            pol_obj.write(pol_id,changes)
            warn("modificat")
        except Exception as e:
            errors.append((pol_id, polissa.name, e))
            warn("Error: polissa {} dona la seguent exepció:",polissa.name)
            print e
    else:
        print str(pol_id) + " " + str(changes)

f = open("killing_maximetre_output.txt","w")
warn("-"*40)
for error in errors:
    print error[0]
    print error[1]
    print error[2]
    print ""
    f.write(str(error)+"\n")
f.close()