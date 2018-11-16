#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import configdb
from consolemsg import step, fail, success, warn, error
from yamlns import namespace as ns
from erppeek import Client

#TODO set up as external parameters using click
# Constants
partner_group_name = 'Energetica'
partner_group_id = 38039            # must exists
category_name = "Energetica"
category_id = 24                    # must exists


# Helpers
def exists(base,index,subindex):
    try:
        value = base[index][subindex]
        assert(type(value) == int)
        return value
    except:
        return None

def listify(iterable,sepparator = ',',head = '[',tail = ']'):
    iterable = [ str(it) for it in iterable]
    return head+sepparator.join(iterable)+tail



# Definitions
step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

doit = '--doit' in sys.argv
warn("l'estat del doit es {}", doit)
verbose = '--verbose' in sys.argv

pol_obj = O.GiscedataPolissa
par_obj = O.ResPartner
add_obj = O.ResPartnerAddress

step("Cercant contractes de {} ...",partner_group_name)
pol_ids = pol_obj.search([('soci', '=', partner_group_id)])
step("{} trobats",len(pol_ids))

step("Cercant titulars, notificdors i pagadors")
pol_vals = pol_obj.read(pol_ids,[
    'titular',
    'pagador',
    'altre_p',
    'direccio_notificacio',
    ])

t_partners_ids = []
n_partners_ids = []
p_partners_ids = []
a_partners_ids = []
addreces_without_parner = []
for pol_val in pol_vals:
    if verbose:
        warn("polissa: "+str(pol_val))
        warn("")
    if exists(pol_val,'titular',0):
        t_partners_ids.append(pol_val['titular'][0])
    if exists(pol_val,'altre_p',0):
        n_partners_ids.append(pol_val['altre_p'][0])
    if exists(pol_val,'pagador',0):
        p_partners_ids.append(pol_val['pagador'][0])
    if exists(pol_val,'direccio_notificacio',0):
        add_vals = add_obj.read(pol_val['direccio_notificacio'][0],['partner_id'])
        if verbose:
            warn("partner de l'adressa de notificacio: "+str(add_vals))
            warn("")
        if exists(add_vals,'partner_id',0):
            a_partners_ids.append(add_vals['partner_id'][0])
        else:
            addreces_without_parner.append(pol_val['id'])

step("titulars ............... {} trobats",len(t_partners_ids))
step("notificadors ........... {} trobats",len(n_partners_ids))
step("pagadors ............... {} trobats",len(p_partners_ids))
step("adreces notificació .... {} trobats",len(a_partners_ids))
step("adreces sense partner .. {} trobats, {}",len(addreces_without_parner),listify(addreces_without_parner))

all_partners_ids = sorted(
    list(set([1] + t_partners_ids + n_partners_ids + p_partners_ids + a_partners_ids)))
step("{} trobats",len(all_partners_ids))

if doit:
    warn("S'aplicara la categoria {} id {} a {} partners",
        category_name,
        category_id,
        len(all_partners_ids))
    success(listify(all_partners_ids))
    par_obj.write(all_partners_ids, {'category_id': [(4, category_id)]})
    success("{} partners updated!",len(all_partners_ids))

success("Final")