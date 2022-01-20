#!/usr/bin/env python
# -*- coding: utf-8 -*-

from erppeek import Client
import configdb
from consolemsg import step, success, error, warn, color, printStdError

def main():
    step("Connectant a l'erp")
    O = Client(**configdb.erppeek)
    success("Connectat a: {}".format(O))
    success("Usuaria: {}".format(O.user))

    fiscal_year_id = O.model('account.fiscalyear').search([('name', 'ilike', '2021')])[0]
    fiscal_year = O.model('account.fiscalyear').browse(fiscal_year_id)

    step("Demanem el balanç per l'any {}".format(fiscal_year.name))

    O.wizard('account.balance.full.report',
             {'form': {'company_id': 1, 'account_list': [[6, 0, []]], 'fiscalyear': fiscal_year_id,
                       'display_account': 'bal_mouvement', 'state': 'none', 'periods': [(6, 0, [])],
                       'all_accounts': True, 'context': {}, 'display_account_level': 5
                       }
              }, 'excelFile_async')

if __name__=='__main__':
    res = main()
    success('Encuat el balanç. Resposta: {}'.format(res))

# vim: et ts=4 sw=4