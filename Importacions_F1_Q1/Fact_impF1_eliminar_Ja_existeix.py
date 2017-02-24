#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

imp_obj = O.GiscedataFacturacioImportacioLinia

imp_ids_no_del = [470571, 468790, 462576, 459709, 456920, 455680, 458431, 457376, 448841, 446859, 446838, 445293, 445102, 433834, 435880, 435575, 443804, 441518, 435379, 436044, 435699, 428398, 393928, 366042, 351351, 348093, 324194, 310987, 279511, 262881, 234356, 218342, 221200, 220413, 217773, 220530, 215933, 218237, 219422, 221949, 214971, 213972, 213157, 185373, 157501, 156467, 106294, 27995]

imp_del_ids = imp_obj.search([('state','=','erroni'),('info','like','Ja existeix una factura'),('id','not in', imp_ids_no_del)])
#imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like','XML erroni')])
imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like',"XML no es correspon al tipus F1")])
imp_del_ids += imp_obj.search([('state','=','erroni'),('info','like',"Document invàlid")])
imp_del_ids_reads = O.GiscedataFacturacioImportacioLinia.read(imp_del_ids,['state','info'])

total = len(imp_del_ids)
n = 0
for imp_del_id in imp_del_ids:
    try:
        imp_obj.unlink([imp_del_id])
        n +=1
        print "%d/%d" % (n,total)
    except Exception, e:
        print e    


print "S'han eliminat %d arxius" % n
