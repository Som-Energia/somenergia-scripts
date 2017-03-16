#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

def posar_tarifes(nom_ajuntament,nom_tarifa,transferencia, tipo de pago, categoria):
    #no remessable no implementat
    from erppeek import Client
    import configdb
    O = Client(**configdb.erppeek)

    pol_obj = O.GiscedataPolissa
    tar_obj = O.ProductPricelist
    ver_obj = O.ProductPricelistVersion
    
    pol_ids = pol_obj.search([('titular.name','=',nom_ajuntament)])
    pol_reads = pol_obj.read(pol_ids,['tarifa'])
    tar_ids = tar_obj.search([('name','like',nom_tarifa)])
    for pol_read in pol_reads:
        tar_id = tar_obj.search([('id','in',tar_ids),
                     ('name','ilike',pol_read['tarifa'][1])
                     ])        
        if not tar_id: 
            print "Polissa {} sense tarifa".format(pol_read['id'])
            continue                
        ver_id = ver_obj.search([('pricelist_id','=',tar_id)])
        if not ver_id: 
            print "Polissa {} sense primera versio tarifa".format(pol_read['id'])
            continue
        pol_obj.write(pol_read['id'],{'llista_preu':tar_id[0],
                                    'versio_primera_factura':ver_id[0],
                                    })
        print pol_read, tar_id, ver_id

posar_tarifes(sys.argv[1], sys.argv[2],1)

#omplir notificador
