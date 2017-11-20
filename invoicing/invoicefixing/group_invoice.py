# -*- coding: utf-8 -*-
import sys
import os
import signal
from datetime import datetime, timedelta

import configdb

from ooop import OOOP
from consolemsg import error
from utils import *
from validacio_eines import adelantar_polissa_endarerida
from display import *

'''
    Agrupació automàtica de factures per a realitzar un sol pagament/cobrament
    1.- Compensar una factura FE amb una AB, en estat obert, amb període i import iguals
    2.- Agrupar totes les factures d'una polissa en un sol pagament de remesa. Tenir en compte IBAN correcte, codi de remesa (paràmetre)
'''
ACC_DEVOLUTIONS = 532

def contractId(gp, contract_name):
    try:
        return gp.search([('name', '=', contract_name)])[0]
    except:
        raise Exception("Contract name not found. Maybe som 0 before",1)

def paymentOrderId(po, po_name, po_type):
    try:
        return po.search([('reference','=',po_name), ('type','=',po_type)])[0]
    except:
        raise Exception("La remesa no existeix o no es del tipus ", po_type)

def facturesObertesDelContracte(ai, gff, contract_name):
    invoices = ai.search([('name', '=', contract_name),('state','=','open')])
    invoices_gisce = []
    total = 0
    for i in invoices:
        gff_id = gff.search([('invoice_id','=',i)])
        invoices_gisce.append(gff_id[0])
        gff_obj = gff.read(gff_id[0])
        ai_obj = ai.read(i)
        #print "Factura %s de %s a %s del tipus %s amb un import de %s." % (str(ai_obj['number']), str(gff_obj['data_inici']), str(gff_obj['data_final']), str(gff_obj['tipo_rectificadora']), str(ai_obj['amount_total']))
        #print "Compara " , ai_obj['account_id'][0], " amb ",ACC_DEVOLUTIONS
        if ai_obj['account_id'][0] == ACC_DEVOLUTIONS:
            raise Exception("Hi ha almenys una factura amb el compte devolucions")
        if gff_obj['tipo_rectificadora'] == 'B':
            total = total - ai_obj['amount_total']
        if gff_obj['tipo_rectificadora'] == 'R':
            total = total + ai_obj['amount_total']
        if gff_obj['tipo_rectificadora'] == 'N':
            total = total + ai_obj['amount_total']

    return invoices_gisce, total

def wizardAgruparFactures(invoices_gisce, total):
    ctx = {
            'model': 'giscedata.facturacio.factura',
            'active_id': invoices_gisce[0],
            'active_ids': invoices_gisce,
            'tz': 'Europe/Madrid',
            'amount_total': total,
            'number_of_invoices': len(invoices_gisce),
           }
    wizard_id = O.WizardGroupInvoicesPayment.create({'amount_total': total , 'number_of_invoices': len(invoices_gisce),},ctx)
    wizard = O.WizardGroupInvoicesPayment.get(wizard_id)
    wizard.group_invoices(ctx)

def wizardFacturesARemesa(invoices_gisce, order_id):
    ctx_po = {
            'model':'giscedata.facturacio.factura',
            'active_id': invoices_gisce[0],
            'active_ids': invoices_gisce,
            'tz': 'Europe/Madrid',
            'domain': [],
            }

    wizard_id_po = O.WizardAfegirFacturesRemesa.create({'order': order_id},ctx_po)#TODO:Get or create remesa de pagament o cobrament
    wizard_po = O.WizardAfegirFacturesRemesa.get(wizard_id_po)
    wizard_po.action_afegir_factures(ctx_po)

def fixIBANInvoice(gp, ai, polissa_id, invoices_ids):
    polissa = gp.get(polissa_id)
    for invoice_id in invoices_ids:
        invoice = ai.get(invoice_id)
        if polissa.bank != invoice.parnter_bank:
            ai.write(invoice_id, {'partner_bank': polissa.bank.id})

def fixIBANPaymentOrder(gp, pl, polissa_id, order_id):
    polissa = gp.get(polissa_id)
    order_lines = pl.search([('order_id','=', order_id)])
    for line_id in order_lines:
        line = pl.get(line_id)
        if polissa.pagador.id == line.partner_id.id:
            if polissa.bank.id != line.bank_id.id:
                pl.write(line_id, {'bank_id': polissa.bank.id})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Grouping invoices')
    parser.add_argument('-rp', '--remesa-pagament')
    parser.add_argument('-rc', '--remesa-cobrament')
    parser.add_argument('-c', '--contracte')
    args = vars(parser.parse_args())
    contract_name = args['contracte']

    O = None
    try:
        O = OOOP(**configdb.ooop)
    except:
        error("Unable to connect to ERP")
        raise

    ai = O.AccountInvoice
    gp = O.GiscedataPolissa
    gff = O.GiscedataFacturacioFactura
    aj = O.AccountJournal
    ap = O.AccountPeriod
    pl = O.PaymentLine
    po = O.PaymentOrder

    contract_id = contractId(gp, contract_name)
    remesa_pagament = paymentOrderId(po, args['remesa_pagament'], 'payable')
    remesa_cobrament = paymentOrderId(po, args['remesa_cobrament'], 'receivable')

    invoices_gisce, total = facturesObertesDelContracte(ai, gff, contract_name)

    print "Total de factures agrupades: ", len(invoices_gisce)
    print "Balanç import total: ", total

    order_id = 0
    if total < 0:
        order_id = int(remesa_pagament)
    elif total > 0:
        order_id = int(remesa_cobrament)
    elif total == 0:
        raise Exception("Cal 'Pagar grup de factures' a mà")

    wizardAgruparFactures(invoices_gisce, total)
    fixIBANInvoice(gp, ai, contract_id, invoices_gisce)

    wizardFacturesARemesa(invoices_gisce, order_id)
    fixIBANPaymentOrder(gp, pl, contract_id, order_id)

# vim: et ts=4 sw=4
