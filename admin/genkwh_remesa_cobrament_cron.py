#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from erppeek import Client
import configdb
import datetime

'''
    Script que agafa les inversions en esborrany i genera les factures de cobrament i les afegeix a la remesa.

    python admin/genkwh_remesa_cobrament_cron.py
'''
def crear_remesa_generation(O):i
    gen = iO.GenerationkwhInvestment
    wiz_gen = O.WizardGenerationkwhInvestmentPayment 
    inv_to_do = gen.search([('draft','=',True)])
    for inv in inv_to_do:
        wiz_gen.do_payment(inv)


#INIT
O = Client(**configdb.erppeek)
crear_remesa_generation(O)

# vim: et ts=4 sw=4
