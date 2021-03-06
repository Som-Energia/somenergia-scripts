# -*- coding: utf-8 -*-
import sys
import os
import signal
from datetime import datetime, timedelta

from consolemsg import error
from utils import *
from validacio_eines import (
    adelantar_polissa_endarerida,
    lazyOOOP,
    )
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

def getPaymentOrder(po, pm, po_type):
    """
    Searches an existing payment order (remesa)
    with the proper payment mode and still in draft.
    """
    if po_type == 'payable':
        mode_name = 'AGRUPACIONS pagar'
    else:
        mode_name = 'AGRUPACIONS cobrar'

    payment_mode_ids = pm.search([
        ('name', '=', mode_name),
        ])

    if not payment_mode_ids:
        raise Exception("La remesa d'agrupació tipus '", po_tytpe, "' no existeix")

    payment_orders = po.search([
        ('mode', '=', payment_mode_ids[0]),
        ('state', '=', 'draft'),
        ])
    if payment_orders:
        return payment_orders[0]

    raise Exception("La remesa d'agrupacions no està creada")
    #TODO: Futur get_or_create_payment_order

def canviCompteDevolucions(ai, ai_obj):
    rp = O.ResPartner
    partner_id = ai_obj['partner_id'][0]
    rp_obj = rp.read(partner_id)
    aa = O.AccountAccount
    ai.write(ai_obj['id'], {'account_id': rp_obj['property_account_receivable'][0]})

def checkNotAllNormal(gff, gp, invoices, contract_name):
    contract_id = contractId(gp, contract_name)
    normal_invoices = gff.search([('state','=','open'), ('polissa_id','=',136154), ('tipo_rectificadora','=','N'), ('type','=','out_invoice')])
    if len(normal_invoices) == len(invoices):
        return False
    else:
        return True

def facturesObertesDelContracte(ai, gff, contract_name, gp):
    invoices = ai.search([('name', '=', contract_name),('state','=','open')])

    if not checkNotAllNormal(gff, gp, invoices, contract_name):
        raise Exception("No hi ha abonadores o rectifidadores, s'ha d'agrupar a mà")

    invoices_gisce = []
    total = 0
    for i in invoices:
        gff_id = gff.search([('invoice_id','=',i)])
        invoices_gisce.append(gff_id[0])
        gff_obj = gff.read(gff_id[0], ['tipo_rectificadora'])
        ai_obj = ai.read(i, ['account_id','amount_total','partner_id'])
        if ai_obj['account_id'][0] == ACC_DEVOLUTIONS:
            canviCompteDevolucions(ai, ai_obj)
        if gff_obj['tipo_rectificadora'] == 'B': #Anuladora amb substitució
            total = total - ai_obj['amount_total']
        if gff_obj['tipo_rectificadora'] == 'A': #Anuladora abono
            total = total - ai_obj['amount_total']
        if gff_obj['tipo_rectificadora'] == 'R': #Rectificadora
            total = total + ai_obj['amount_total']
        if gff_obj['tipo_rectificadora'] == 'N': #Normal
            total = total + ai_obj['amount_total']

    return invoices_gisce, total

def wizardAgruparFactures(O, invoices_gisce, total):
    ctx = {
            'model': 'giscedata.facturacio.factura',
            'active_id': invoices_gisce[0],
            'active_ids': invoices_gisce,
            'tz': 'Europe/Madrid',
            'amount_total': total,
            'number_of_invoices': len(invoices_gisce),
           }
    wizard_id = O.WizardGroupInvoicesPayment.create({'amount_total': total , 'number_of_invoices': len(invoices_gisce),},ctx)
    #wizard = O.WizardGroupInvoicesPayment.get(wizard_id) #Create return the wizard itself, not the ID
    return wizard_id.group_invoices()

def wizardFacturesARemesa(O, invoices_gisce, order_id):
    ctx_po = {
            'model':'giscedata.facturacio.factura',
            'active_id': invoices_gisce[0],
            'active_ids': invoices_gisce,
            'tz': 'Europe/Madrid',
            'domain': [],
            }

    wizard_id = O.WizardAfegirFacturesRemesa.create({'order': order_id},ctx_po)#TODO:Get or create remesa de pagament o cobrament
    #wizard_po = O.WizardAfegirFacturesRemesa.get(wizard_id) #Create return the wizard itself, not the ID
    return wizard_id.action_afegir_factures()

def conciliarFactures(ai, ap, aj, invoices_gisce):
    period_id = getPeriodId(ap)
    pay_journal_id = 5 #Jornal Client invoices "Factures Energia"
    journal = aj.read(pay_journal_id)
    pay_account_id = journal['default_credit_account_id'][0]
    writeoff_acc_id = False
    writeoff_journal_id = False
    writeoff_period_id = False
    context = {}
    name = 'Pagament de factures conciliades'

    for inv_id in invoices_gisce:
        inv = ai.read(inv_id)
        pay_amount = inv['amount_total']
        pay_account_id = inv['account_id'][0]
        print "Cridem al pay and reconcile: ", inv_id, pay_amount, pay_account_id, period_id, pay_journal_id, writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context, name
        ai.pay_and_reconcile([inv_id],
                 pay_amount,
                 pay_account_id,
                 period_id,
                 pay_journal_id,
                 writeoff_acc_id,
                 writeoff_period_id,
                 writeoff_journal_id,
                 context,
                 name)

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
    return True

def do(O, contract_name):
    ai = O.AccountInvoice
    gp = O.GiscedataPolissa
    gff = O.GiscedataFacturacioFactura
    aj = O.AccountJournal
    ap = O.AccountPeriod
    pl = O.PaymentLine
    po = O.PaymentOrder
    pm = O.PaymentMode

    contract_id = contractId(gp, contract_name)
    remesa_pagament = getPaymentOrder(po, pm, 'payable')
    remesa_cobrament = getPaymentOrder(po, pm, 'receivable')

    invoices_gisce, total = facturesObertesDelContracte(ai, gff, contract_name, gp)

    print "Total de factures per agrupar: ", len(invoices_gisce)
    print "Balanç import total: ", total

    order_id = 0
    if total < 0:
        order_id = int(remesa_pagament)
    elif total > 0:
        order_id = int(remesa_cobrament)
    elif total == 0:
        raise Exception("Cal 'Pagar grup de factures' a mà")

    agrupades = wizardAgruparFactures(O, invoices_gisce, total)
    #fixIBANInvoice(gp, ai, contract_id, invoices_gisce)
    print "Factures agrupades: ", invoices_gisce

    remesades = wizardFacturesARemesa(O, invoices_gisce, order_id)
    print "Factures afegides a la remesa ", order_id

    output = fixIBANPaymentOrder(gp, pl, contract_id, order_id)
    print "Result: ", output

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Grouping invoices')
    parser.add_argument('-c', '--contracte')
    args = vars(parser.parse_args())
    contract_name = args['contracte']

    O = lazyOOOP()

    do(O, contract_name)


# vim: et ts=4 sw=4
