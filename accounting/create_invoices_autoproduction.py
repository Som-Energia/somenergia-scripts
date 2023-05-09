#!/usr/bin/env python
# -*- coding: utf-8 -*-
import StringIO
import csv
import sys
from erppeek import Client
import configdb
from datetime import datetime, date

O = Client(**configdb.erppeek)

## SYNTAX
# script.py inscripcions.csv
DESC_MANAGE = { "ca_ES" : 'Despeses de Som Energia per la organització i gestió de la compra conjunta',
        "es_ES" : 'Gastos de Som Energia para la organización y gestión de la compra conjunta'}
DESC_ADVANCE = { "ca_ES" : '1r pagament a compte Enginyeria',
        "es_ES" : '1r pago a cuenta de la Ingenieria'}

class InvoiceMaker:
    def __init__(self, O, dni_list):
        self.O = O
        self.dni_list = dni_list

    def getValsInvoice(self, dni):
        partner_id = self.O.ResPartner.search([('vat','=',"ES"+dni)])
        if not partner_id:
            print "La inscripció amb DNI ", dni, " no existeix al ERP, no s'ha fet factura"
            return None

        date_invoice = str(date.today())
        account_id = self.O.AccountAccount.search([('code','=','430000000000')])
        journal_id = self.O.AccountJournal.search([('code','=','VENTA')])
        payment_type_id = self.O.PaymentType.search([('code','=','TRANSFERENCIA_CSB')])
        ai_obj = self.O.AccountInvoice

        vals = {}
        vals.update(ai_obj.onchange_partner_id([], 'out_invoice', partner_id[0]).get('value', {}))
        vals.update({
            'partner_id': partner_id[0],
            'type': 'out_invoice',
            'journal_id': journal_id[0],
            'account_id': account_id[0],
            'payment_type': payment_type_id[0],
            'date_invoice': date_invoice,
        })
        return vals

    def getValsLine(self, invoice_id, account_name, line_name, price_unit):
        account_id = self.O.AccountAccount.search([('code','=',account_name)])
        tax_id = self.O.AccountTax.search([('name','=','IVA 21% (Vendes)')])
        line = dict(
            invoice_id = invoice_id,
            name = line_name,
            quantity = 1,
            price_unit = price_unit,
            account_id = account_id[0],
            invoice_line_tax_id = [(6,0,tax_id)],
        )
        return line

    def getValsLineRounding(self, invoice_id, account_name, line_name, price_unit):
        account_id = self.O.AccountAccount.search([('code','=',account_name)])
        line = dict(
            invoice_id = invoice_id,
            name = line_name,
            quantity = -1,
            price_unit = price_unit,
            account_id = account_id[0],
        )
        return line

    def getValsLine_without_tax(self, invoice_id, account_name, line_name, price_unit):
        account_id = self.O.AccountAccount.search([('code','=',account_name)])
        line = dict(
            invoice_id = invoice_id,
            name = line_name,
            quantity = 1,
            price_unit = price_unit,
            account_id = account_id[0],
        )
        return line

    def makeInvoice(self, dni):
        vals = self.getValsInvoice(dni)
        if not vals:
            return None
        invoice = self.O.AccountInvoice.create(vals)
        partner_lang = self.O.ResPartner.read(vals['partner_id'], ['lang'])['lang']
        valsLineManage = self.getValsLine(invoice.id, '705000000100',
                DESC_MANAGE[partner_lang], 82.65)
        invoice_line_services = self.O.AccountInvoiceLine.create(valsLineManage)
        valsLineRounding = self.getValsLineRounding(invoice.id, '626000000005', 'Ajust factura', 0.01)
        self.O.AccountInvoiceLine.create(valsLineRounding)
        #valsLineAdvance = self.getValsLine_without_tax(invoice.id, '419000000001', DESC_ADVANCE[partner_lang], 100.00)
        #invoice_line_services = self.O.AccountInvoiceLine.create(valsLineAdvance)
        self.O.AccountInvoice.button_reset_taxes([invoice.id])
        return True

    def makeInvoices(self):
        n_invoices = 0
        for dni in self.dni_list:
            invoice_created = self.makeInvoice(dni)
            if invoice_created:
                n_invoices += 1
        print "S'han creat ", n_invoices , " factures."

enrolment_file =  sys.argv[1]
dni_list = []

with open(enrolment_file, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    next(reader)
    for row in reader:
        if row[0] and not row[1]:
            dni_list.append(row[6].upper())

im = InvoiceMaker(O, dni_list)
im.makeInvoices()
