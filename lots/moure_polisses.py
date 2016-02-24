# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

id_lot_orig = O.GiscedataFacturacioLot.search([('state','=','obert')])[0]
id_lot_dest = id_lot_orig + 1

id_clot = O.GiscedataFacturacioContracte_lot.search([
    ('lot_id', '=', id_lot_orig),
    ('state', 'in', ('esborrany', 'obert'))
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
    
# Posar lot a les polisses que no tinguin lot
posar_lot_a_polisses_sense_lot = False
if posar_lot_a_polisses_sense_lot:
    for pol_id in O.GiscedataPolissa.search([('lot_facturacio','=',0),('state','=','activa')]):
        pol = O.GiscedataPolissa.get(pol_id)
        pol.write({'lot_facturacio': id_lot_dest})
    print 'Pòlissa id %s' % pol_id

O.GiscedataFacturacioLot.update_progress([id_lot_dest] + [id_lot_orig])