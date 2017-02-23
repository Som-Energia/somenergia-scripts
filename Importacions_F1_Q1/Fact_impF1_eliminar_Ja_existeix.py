#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

imp_obj = O.GiscedataFacturacioImportacioLinia

#imp_del_ids = imp_obj.search([('state','=','erroni'),('info','=','Aquest fitxer XML ja s\'ha processat en els següents IDs')])
#imp_del_ids = imp_obj.search([('state','=','erroni'),('info','=','Ja existeix una factura amb el mateix origen')])


#imp_del_ids = imp_obj.search([('state','=','erroni'),('info','like','Ja existeix una factura')])
imp_del_ids = imp_obj.search([('state','=','erroni'),('info','like','XML erroni')])
imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like',"XML no es correspon al tipus F1")])
imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like',"Document invàlid")])
im_del_ids_reads = O.GiscedataFacturacioImportacioLinia.read(imp_del_ids,['state','info'])

total = len(imp_del_ids)
n = 0

for imp_del_id in imp_del_ids:
    try:
        print im_del_ids_reads
        imp_obj.unlink([imp_del_id])
        n +=1
        print "%d/%d" % (n,total)
    except Exception, e:
        print e    

