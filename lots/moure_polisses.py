#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

id_lot_orig = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
id_lot_dest = id_lot_orig + 1

id_clot = O.GiscedataFacturacioContracte_lot.search([
    ('lot_id', '=', id_lot_orig),
    ('state', 'in', ('esborrany', 'obert','facturat'))
])
ids_poli = O.GiscedataFacturacioContracte_lot.read(id_clot, ['polissa_id', 'state'])

n=0
total = len(ids_poli)

for clot in ids_poli:
    print 'Pòlissa %s' % clot['polissa_id'][1]
    O.GiscedataPolissa.write(clot['polissa_id'][0], {'lot_facturacio': id_lot_dest})
    if clot['state'] != 'esborrany':
        O.GiscedataFacturacioContracte_lot.unlink([clot['id']])
    n += 1
    print "                       %d/%d" % (n,total)
    

# Posar lot a les polisses que no tinguin lot pero no tingui R1 obert
sw_ids = O.GiscedataSwitching.search([('proces_id.name','=','R1'),
                                        ('state','=','open')])
sw_reads = O.GiscedataSwitching.read(sw_ids,['cups_polissa_id'])
pol_sw_ids = [a['cups_polissa_id'][0] for a in sw_reads if a['cups_polissa_id']]

pol_ids = O.GiscedataPolissa.search([('id','not in',pol_sw_ids),
                                     ('lot_facturacio','=',0),
                                     ('state','=','activa')])
pol_ids += O.GiscedataPolissa.search([('lot_facturacio','<',id_lot_orig),
                                       ('state','=','activa')])
for pol_id in pol_ids:
    pol = O.GiscedataPolissa.get(pol_id)
    pol.write({'lot_facturacio': id_lot_dest})
print 'Pòlissa id %s' % pol_id

O.GiscedataFacturacioLot.update_progress([id_lot_dest] + [id_lot_orig])
