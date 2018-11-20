#!/usr/bin/env python


import erppeek
import dbconfig

import time
from yamlns import namespace as ns

t0 = time.time()

erp = erppeek.Client(**dbconfig.erppeek)


users = erp.ResPartner.read(range(100),[])

print("Reading 100 Partners {}".format(time.time()-t0))

t0 = time.time()
contracts = erp.GiscedataPolissa.read(range(100),[])
print("Reading 100 Contracts {}".format(time.time()-t0))

users = ns.loads(ns(users=users).dump())
#print users.users[2].dump()



#vim: ts=4 sw=4 noet
