#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
#Aquest escript serveix per eliminar les polisses que actualment són baixa
# del lot actual,, encara que no tinguin lot escrit a la polissa
# Devegades (hauriem de descorbri el motiu) es colen dintre al lot de facturacio

O = OOOP(**configdb.ooop)

baixes_ids = O.GiscedataPolissa.search([('active','=',0)])
baixes_lot_ids = O.GiscedataFacturacioContracte_lot.search([('state','=','obert'),('polissa_id','in',baixes_ids)])
count = 0

for baixa_lot_id in baixes_lot_ids:
    baixa_lot = O.GiscedataFacturacioContracte_lot.get(baixa_lot_id)
    count += 1
    print str(count)+ '  -->   ' + str(baixa_lot.polissa_id.name)
    baixa_lot.unlink()

#Comprovació que no tenen lot escrita a la polissa, encara que estiguin dintre de les polisses en lot
baixes_amb_lot =[]
baixes_id=[]
for n in range(len(O.GiscedataFacturacioContracte_lot.read(baixes_lot_ids,['polissa_id']))):
    baixes_amb_lot.append(O.GiscedataFacturacioContracte_lot.read(baixes_lot_ids,['polissa_id'])[n]['polissa_id'][1])
    baixes_id.append(O.GiscedataFacturacioContracte_lot.read(baixes_lot_ids,['polissa_id'])[n]['polissa_id'][0])
    
