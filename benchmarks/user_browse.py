#!/usr/bin/env python
# -*- encoding: utf-8 -*-


import erppeek
import dbconfig

import time
from yamlns import namespace as ns
import sys
from consolemsg import step, error, warn, success


nregistres = sys.argv[1] if len(sys.argv)>1 else 100


step("Connectant a {server}",**dbconfig.erppeek)
t0 = time.time()
erp = erppeek.Client(**dbconfig.erppeek)

success("Establir connexió: {}", time.time()-t0)

t0 = time.time()

users = erp.ResPartner.read(range(100),[])

success("Llegir {} Partners {}",nregistres, time.time()-t0)

t0 = time.time()
contracts = erp.GiscedataPolissa.read(range(100),[])
success("Llegir {} Contractes {}",nregistres, time.time()-t0)


#users = ns.loads(ns(users=users).dump())
#print users.users[2].dump()



#vim: ts=4 sw=4 noet
