# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

imp_obj = O.GiscedataFacturacioImportacioLinia

imp_del_ids = imp_obj.search([('state','=','erroni'),('info','like','Ja existeix una factura')])
imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like','XML erroni')])
imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like',"XML no es correspon al tipus F1")])
imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like',"Document invàlid")])

total = len(imp_del_ids)
n = 0

for imp_del_id in imp_del_ids:
    try:
        imp_obj.unlink([imp_del_id])
        n +=1
        print "%d/%d" % (n,total)
    except Exception, e:
        print e    
