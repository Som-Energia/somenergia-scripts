#!/usr/bin/env python
# -*- coding: utf8 -*-
from validacio_eines import (
    lazyOOOP
        )
from consolemsg import step, fail, success, warn, error
from yamlns import namespace as ns

O = lazyOOOP()
Invoice = O.GiscedataFacturacioFactura
Polissa = O.GiscedataPolissa

def checkDateLecturaPolissa(polissa):
    AB_ids = Invoice.search([
        ('type','in',['out_refund']),
        ('polissa_id','=',polissa['id'])
        ])
    FE_ids = Invoice.search([
       ('type','in',['out_invoice']),
       ('polissa_id','=',polissa['id'])
        ])
    if AB_ids:
        FE_AB_refs = Invoice.read(AB_ids, ['ref'])
        FE_AB_ids = [x['ref'][0] for x in FE_AB_refs]
        FE_clean_ids = list(set(set(FE_ids) - set(FE_AB_ids)))
    else:
        FE_clean_ids = FE_ids
    if FE_clean_ids:
        last_FE_id = Invoice.search([
                ('id','in', FE_clean_ids)],
                order = 'data_final desc')[0]
        last_FE = Invoice.read(last_FE_id,['data_final'])
        last_FE_data_final = last_FE['data_final']
    else:
        last_FE_data_final = None

    if last_FE_data_final != polissa['data_ultima_lectura']:
        step('Factura FE o RE fecha diferente a data última lectura')
        return True
    return False

def hasDraftABInvoice(polissa):
    AB_ids = Invoice.search([
        ('type','in',['out_refund']),
        ('polissa_id','=',polissa['id']),
        ('state','=','draft')
        ])
    return len(AB_ids) > 0


def checkDateLecturaPolissaB(polissa):
    ko = False
    #polissa = Polissa.read(polissa,[
    #    'id',
    #    'data_ultima_lectura',
    #    ])[0]
    polissa = ns(polissa)
    step('Comprobando invoices en borrador de pol', polissa.id)
    invoices = get_invoices_from_polissa(polissa)
    invoices = Invoice.read(invoices,[
        'id',
        'type',
        'data_final',
        ])
    last_invoice = ns(invoices[0])
    step('facturas en borrador:', invoices)
    if last_invoice.type == 'out_invoice':
        if last_invoice.data_final != polissa.data_ultima_lectura:
            step('Factura FE o RE fecha diferente a data última lectura')
            ko = True
    if last_invoice.type == 'out_refund':
        last_invoice_not_AB = ns(get_last_invoice_not_AB(invoices))
        if last_invoice_not_AB.data_final != polissa.data_ultima_lectura:
            step('Factura AB con fecha diferente a data última lectura')
            ko = True
    return ko

def get_invoices_from_polissa(polissa):
    return Invoice.search([
        ('type','in',['out_refund','out_invoice']),
        ('polissa_id','=',polissa['id'])
        ])
def get_last_invoice_not_AB(invoices):
    count_AB = 0
    for elem in invoices:
        if ns(elem).type == 'out_refund':
            count_AB += 1
        if count_AB >= 0 and ns(elem).type == 'out_invoice':
            count_AB -=1
        if count_AB < 0:
            return elem

#polissa = O.GiscedataPolissa.search([('id','=','00046')])
#pol = Polissa.read(165,['name','data_alta','tarifa','comptadors','data_ultima_lectura','lot_facturacio','pagador','cups',])
#print hasDraftABInvoice(pol)
#print checkDateLecturaPolissa(pol)
