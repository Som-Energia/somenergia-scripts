# -*- coding: utf-8 -*-
import sys
import os


def show_contract_status(contract,status):
    out = "## POLISSA {contract} STATUS: {status}\n".format(**locals())
    return out


def show_invoice(polissa_id, lects, header, n):
    out = "------------ {header} ------ [{polissa_id}] ---------\n".format(**locals())
    try:

        for idx in range(n):
            out += '[{idx}] {date} {periode} {lectura} {origen}\n'.format(**{'idx': idx,
                                                                  'date': lects[idx]['name'],
                                                                  'periode': lects[idx]['periode'][1],
                                                                  'lectura': lects[idx]['lectura'],
                                                                  'origen': lects[idx]['origen_id'][1] })
    except Exception, e:
        pass
    return out


def show_results(invoices, quarantine):
    out = 'S\'han anul.lat les factures de %s a %s per un import de %d€. S\'ha emès una factura per un import de %d€\n' % (
        invoices[1]['data_inici'],
        invoices[1]['data_final'],
        invoices[1]['amount_total'],
        invoices[0]['amount_total'])
    out += 'Se han anulado las facturas de %s a %s por un importe de %d€. Se ha emitido una factura por un importe de %d€\n' % (
        invoices[1]['data_inici'],
        invoices[1]['data_final'],
        invoices[1]['amount_total'],
        invoices[0]['amount_total'])

    if quarantine['kWh']:
        out += 'Consum diari 5 vegades superior a històric\n'
        out += 'Consum diari 5 vegades superior a històric\n'
    if quarantine['euro']:
        out += 'Import 2 vegades superior a històric\n'
        out += 'Importe 2 veces superior al histórico\n'
    return out
