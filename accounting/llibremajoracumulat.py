#!/usr/bin/env python
#-*- coding: utf-8 -*-
from erppeek import Client
import sys
import base64
from subprocess import call
import time
import configdb
from consolemsg import error, step, success, warn

def fail(msg, *args, **params):
    error(msg, *args, **params)
    exit(-1)

report = 'account.general.ledger.cumulative'
outputFile = sys.argv[1]
account = sys.argv[2] if len(sys.argv)>2 else [1703] # 572000000002
start_date = sys.argv[3]
end_date = sys.argv[4]
state = 'bydate' # 'none' # 'none' tots , 'bydate': per dates

step("Connecting to {server}",**configdb.erppeek)

O = Client(**configdb.erppeek)

step("Identifying account named '{}'", account)

ids = O.AccountAccount.search([
    ('code','=',account),
    ])

ids or fail("Compte '{}' no trobat", account)
success("Found account id = {}", ids)

step("Identifying the fiscal year '{}'", start_date[:4])
fiscalyear_ids = O.AccountFiscalyear.search([
    ('code','=',start_date[:4]),
    ])

fiscalyear_ids or fail("No he trobat l'any fiscal per {}", start_date[:4])
len(fiscalyear_ids)==1 or warn("Hi ha mes d'un any fiscal amb codi {}", start_date[:4])
success("Using fiscal year id {}", fiscalyear_ids[0])

step("Generating report between {} and {}", start_date, end_date)


params = {
   'report_type': 'pdf', 
   'form': {
        'sortbydate': 'sort_date',
        'periods': [[6, 0, []]],
        'date_from': start_date,
        'date_to': end_date,
        'landscape': False,
        'initial_balance': False,
        'company_id': 1,
        'state': state,
        'context': {
            'lang': 'ca_ES',
            'active_ids': [158],
            'tz': 'Europe/Madrid',
            'active_id': 158
        },
        'amount_currency': False,
        'display_account': 'bal_mouvement',
        'fiscalyear': fiscalyear_ids[0],
    },
    'model': 'account.account',
    'report_id': False,
    'id': ids[0]
}

report_id = O.report(report, ids, params, {'lang': 'ca_ES', 'tz': 'Europe/Madrid'})
sys.stdout.write("Waiting")
res = {'state': False}
while not res['state']:
    res = O.report_get(report_id)
    sys.stdout.write(".")
    time.sleep(0.2)
    sys.stdout.flush()

sys.stdout.write("\n")
	

with open(outputFile,'w') as f:
    f.write(base64.b64decode(res['result']))

