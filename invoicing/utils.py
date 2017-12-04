# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime, timedelta

DAYS_PER_MONTH=30.0


def pay_invoice(O, invoice_id, rectificar):
    #action = 'rectificar' if rectificar else 'anullar'
    wiz_id = O.WizardRanas.create({},{'active_ids': [invoice_id]})
    wiz = O.WizardRanas.get(wiz_id)
    if rectificar:
        return wiz.action_rectificar({'active_ids': [invoice_id]})
    return wiz.action_anullar({'active_ids': [invoice_id]})


def get_contract_daily_consumption(O, contract_id):
    return O.GiscedataPolissa.consum_diari(contract_id)


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


def read_contracts(O, contracts_id, fields):
    return O.GiscedataPolissa.read(contracts_id, fields)


def get_contracts(O, search_pattern, fields, active_test=True):
    contracts_id = O.GiscedataPolissa.search(search_pattern, 0, 0, False, {'active_test': active_test})
    if fields is None:
        return contracts_id

    return read_contracts(O, contracts_id, fields)


def read_measures(O, measures_id, fields, pool=False):
    obj = O.GiscedataLecturesLecturaPool if pool else O.GiscedataLecturesLectura
    return obj.read(measures_id, fields)


def get_measures(O, search_pattern, fields, pool=False, active_test=True):
    obj = O.GiscedataLecturesLecturaPool if pool else O.GiscedataLecturesLectura
    measures_id = obj.search(search_pattern, 0, 0, False, {'active_test': active_test})
    if fields is None:
        return measures_id

    return read_measures(O, measures_id, fields, pool)


def update_measures(O, measures_id, values, pool=False):
    obj = O.GiscedataLecturesLecturaPool if pool else O.GiscedataLecturesLectura
    return obj.write(measures_id, values)


def read_meters(O, meters_id, fields):
    return O.GiscedataLecturesComptador.read(meters_id, fields)


def get_meters(O, search_pattern, fields, active_test=True):
    meters_id = O.GiscedataLecturesComptador.search(search_pattern, 0, 0, False, {'active_test': active_test})
    if fields is None:
        return meters_id

    return read_meters(O, meters_id, fields)


def read_invoices(O, invoices_id, fields):
    return O.GiscedataFacturacioFactura.read(invoices_id, fields)


def get_invoices(O ,search_pattern, fields, active_test=True):
    invoices_id = O.GiscedataFacturacioFactura.search(search_pattern, 0, 0, False, {'active_test': active_test})
    if fields is None:
        return invoices_id

    return read_invoices(invoices_id, fields)


def get_measures_by_meter(O, meter_id, mtype, pool=False, start_date=None):
    obj = O.GiscedataLecturesLecturaPool if pool else O.GiscedataLecturesLectura
    fields_to_search = [('comptador', '=', meter_id),
                        ('origen_id', 'in', mtype)]
    if start_date:
        fields_to_search.append(('name', '>', start_date))
    measures_id = obj.search(fields_to_search)
    return obj.read(measures_id, ['id', 'name'])


def get_measures_by_contract(O, contract_id, mtype, pool=False, start_date=None):
    obj = O.GiscedataLecturesLecturaPool if pool else O.GiscedataLecturesLectura
    fields_to_search = [('comptador.polissa', '=', contract_id),
                        ('origen_id', 'in', mtype)]
    if start_date:
        fields_to_search.append(('name', '>', start_date))
    measures_id = obj.search(fields_to_search)
    return obj.read(measures_id, ['id', 'name', 'origen_id'])


def load_new_measure(O, measure_id):
    ctx = {'active_id': measure_id}
    wiz_id = O.WizardCopiarLecturaPoolAFact.create({},ctx)
    O.WizardCopiarLecturaPoolAFact.action_copia_lectura([wiz_id], ctx)
    return


def load_new_measures(O, contract_id, mtype=range(1,7)+[8], start_date=None):
    meters_id = O.GiscedataLecturesComptador.search([('polissa', '=', contract_id)])
    new_measures = []
    for meter_id in meters_id:
        invoice_measures = get_measures_by_meter(O, meter_id, range(1,12), pool=False)
	if not invoice_measures:
            print "Sense lectures a comptador id: "+str(meter_id)
            continue
        new_measures += get_measures_by_meter(O, meter_id, mtype, True, invoice_measures[0]['name'])
    for new_measure in new_measures:
        load_new_measure(O, new_measure['id'])
    return new_measures


def get_contract_status(O, contract_id):
    contract = O.GiscedataPolissa.read(contract_id, ['cups'])

    sws_id = O.GiscedataSwitching.search([('cups_id', '=', contract['cups'][0]),
                                          ('proces_id.name', 'in', ('C1', 'C2')),
                                          ('step_id.name', 'in', ('06', '11'))])
    if len(sws_id) > 0:
        return 'CX 06-11'

    sws_id = O.GiscedataSwitching.search([('cups_id', '=', contract['cups'][0]),
                                          ('proces_id.name','like','B')])

    if len(sws_id) > 0:
        return 'BX'


    limit_date = datetime.today()-timedelta(days=21)
    invoices_id = O.GiscedataFacturacioFactura.search([('polissa_id','=',contract_id),
                                                       ('invoice_id.type', 'in', ['out_invoice','out_refund']),
                                                       ('invoice_id.state', '=', 'open'),
                                                       ('invoice_id.date_invoice', '<', limit_date.strftime('%Y-%m-%d'))])

    if len(invoices_id):
        return 'UNPAID'

    return 'OK'

def open_and_send(O, ids, lang, send_refund=True, send_rectified=True, send_digest=False, num_contracts=1):
    ctx = {
	    'active_id': ids[0],
	    'active_ids': ids,
            'lang': lang,
	    'tz': 'Europe/Madrid'
           }
    vals = {
            'state': 'init',
            'send_refund': send_refund,
            'send_rectified': send_rectified,
            'send_digest': send_digest,
            'num_contracts': num_contracts,
        }
    wizard_id = O.WizardInvoiceOpenAndSend.create(vals, ctx)
    wizard = O.WizardInvoiceOpenAndSend.get(wizard_id)
    wizard.action_obrir_i_enviar(ctx)

def getPeriodId(period_obj):
    period_name = datetime.today().strftime('%m/%Y')
    return period_obj.search([('name','=',period_name)])[0]
    

# vim: et ts=4 sw=4
