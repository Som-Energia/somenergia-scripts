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
#print checkDateLecturaPolissa(polissa)
