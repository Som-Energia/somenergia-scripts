# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime, timedelta

DAYS_PER_MONTH=30.0

def pay_invoice(O, invoice_id, rectificar):
    action = 'rectificar' if rectificar else 'anullar'
    wiz = O.WizardRanas.new()
    wiz_id = wiz.save()

    print "Applying {action} on {invoice_id}".format(**locals())
    return wiz._action(action,{'active_ids': [invoice_id]})


def get_contract_amount_mean(O, polissa_id):
    def months_between(d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)/DAYS_PER_MONTH # Aprox

    invoices_id = O.GiscedataFacturacioFactura.search([('polissa_id', '=', polissa_id),
                                                       ('type', '=', 'out_invoice')])
    invoices = O.GiscedataFacturacioFactura.read(invoices_id, ['data_inici', 'data_final', 'amount_total'])
    n_months = 0
    total_amount = 0
    for invoice in invoices:
        n_months += months_between(invoice['data_inici'], invoice['data_final'])
        total_amount += invoice['amount_total']
    return total_amount/n_months

