#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from consolemsg import step, success
from datetime import datetime, timedelta
from yamlns import namespace as ns


O = Client(**configdb.erppeek)
success("connected!")

pol_obj = O.GiscedataPolissa
fac_obj = O.GiscedataFacturacioFactura


def isodate(adate):
    return adate and datetime.strptime(adate, '%Y-%m-%d')


def check_last_modcon_breaks_invoicing_cycle(polissa, invoice_date_end):

    def dateplus(adate, adddays=1):
        return (datetime.strptime(adate, '%Y-%m-%d') + timedelta(days=adddays)).strftime('%Y-%m-%d')

    invoicing_break_fields = set([
        'autoconsumo',
        'tensio',
        'mode_facturacio',
        'tarifa',
        'potencia',
        'titular'
    ])

    if polissa.modcontractual_activa.data_inici != dateplus(invoice_date_end):
        return False

    if not polissa.modcontractuals_ids or len(polissa.modcontractuals_ids) <= 1:
        return False

    changed_keys = set(polissa.get_changes({'modcon_id': polissa.modcontractual_activa.modcontractual_ant.id}).keys())
    if len(changed_keys) == 0:
        return False

    return len(changed_keys & invoicing_break_fields) != 0


def check_delayed_invoices_when_MODCON_mc03(polissa_id, delayed_limit):
    """Detect a polissa with a modification and only one short invoice that breaks the incoicing cicle"""
    """
    - short "out_invoice" "draft" invioces (<= 25 days)
    - only one invoice
    - contract has a modification with the invoice end date
    - contract is not finished in the invoice end date
    """
    checked_invoice_ids = []

    polissa = pol_obj.browse( polissa_id)

    delayed_invoices = []
    draft_invoices_ids = fac_obj.search([('polissa_id', '=', polissa_id), ('state', '=', 'draft'), ('type', '=', 'out_invoice')])
    if draft_invoices_ids:
        draft_invoices_data = fac_obj.read(draft_invoices_ids, ['data_inici', 'data_final'])

        for draft_invoice_data in draft_invoices_data:
            if (isodate(draft_invoice_data['data_final']) - isodate(draft_invoice_data['data_inici'])).days <= delayed_limit:
                delayed_invoices.append(draft_invoice_data)

            if (len(delayed_invoices) == 1 and
                polissa.data_baixa != delayed_invoices[0]['data_final'] and
                check_last_modcon_breaks_invoicing_cycle(polissa, delayed_invoices[0]['data_final'])):
                    checked_invoice_ids.append(delayed_invoices[0]['id'])

    return checked_invoice_ids


def seach_polisses_with_daft_invoices():
    draft_invoices_ids = fac_obj.search([('state', '=', 'draft'), ('type', '=', 'out_invoice')])
    fac_data = fac_obj.read(draft_invoices_ids,['polissa_id'])
    return sorted(list(set([f['polissa_id'][0] for f in fac_data])))
    

def get_hit_data(pol_id, fac_id):
    data = {}
    data_polissa = pol_obj.read(pol_id,['name'])
    data['polissa'] = data_polissa['name']
    data['factura'] = fac_id
    data_factura = fac_obj.read(fac_id[0], ['data_inici', 'data_final'])
    data['inici'] = data_factura['data_inici']
    data['fi'] =  data_factura['data_final']
    return data

def get_validation_hits(delayed_limit):
    noFactures = False

    pol_ids = seach_polisses_with_daft_invoices()
    for pol_id in pol_ids:
        fac_ids = check_delayed_invoices_when_MODCON_mc03(pol_id, delayed_limit)

        if fac_ids:
            data = get_hit_data(pol_id,fac_ids)
            step("La polissa {polissa} te una factura en esborrany que trenca el cicle de facturacio: id factura {factura} periode {inici} fins {fi}",**data)
        else:
            noFactures = True

    if noFactures:
        step("No hi ha factura que trenqui el cicle de facturacio")


def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'delayed_limit',
        type=int,
        help="dies maxims",
        )
    return parser.parse_args(namespace=ns())

def main():
    args = parseArguments()
    get_validation_hits(**args)

if __name__ == '__main__':
    main()

# vim: et ts=4 sw=4
