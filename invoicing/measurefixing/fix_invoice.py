#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
import os
from datetime import datetime, timedelta

O = OOOP(**configdb.ooop)

def dump(polissa_id, lects, header, n):
    try:
        print '------------ {header} ------ [{polissa_id}] ---------'.format(**locals())
        for idx in range(n):
            print '[{idx}] {date} {periode} {lectura} {origen}'.format(**{'idx': idx,
                                                                  'date': lects[idx]['name'],
                                                                  'periode': lects[idx]['periode'][1],
                                                                  'lectura': lects[idx]['lectura'],
                                                                  'origen': lects[idx]['origen_id'][1] })
    except Exception as e:
        pass

def payInvoice(invoice_id, rectificar):
    action = 'anullar'
    if rectificar:
        action = 'rectificar'
    wiz = O.WizardRanas.new()
    wiz_id = wiz.save()

    print "Applying {action} on {invoice_id}".format(**locals())
    return wiz._action(action,{'active_ids': [invoice_id]})


def get_contract_amount_mean(polissa_id):
    def months_between(d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)/30.0  # Aprox

    invoices_id = O.GiscedataFacturacioFactura.search([('polissa_id', '=', polissa_id),
                                                       ('type', '=', 'out_invoice')])
    invoices = O.GiscedataFacturacioFactura.read(invoices_id, ['data_inici', 'data_final', 'amount_total'])
    n_months = 0
    total_amount = 0
    for invoice in invoices:
        n_months += months_between(invoice['data_inici'], invoice['data_final'])
        total_amount += invoice['amount_total']
    return total_amount/n_months



def fix_contract(polissa_id, quarantine):
    lects_id = O.GiscedataLecturesLectura.search([('comptador.polissa', '=' , polissa_id)])
    lects = O.GiscedataLecturesLectura.read(lects_id, ['name', 'periode', 'lectura', 'origen_id', 'observacions'])
    offset_ct = {'2.0A (P1)': 1, '2.1A (P1)': 1,
                 '2.0DHA (P1)': 2, '2.1DHA (P1)': 2, '2.1DHS (P1)': 2}

    dump(polissa_id, lects, None, 10)

    if len(lects) < 2:
        return

    for back_idx in reversed(range(1, 15)):
        if not lects[0]['periode'][1].startswith('2'):
            # 3.0 pending
            continue

        offset = offset_ct[lects[0]['periode'][1]]
        try:
            def check_origen(lects, n, origen):
                for idx in range(1, n+1):
                    if not lects[idx]['origen_id'][1] == origen:
                        return False
                return True

            prev_idx = back_idx*offset
            last_idx = offset + prev_idx

#            if (not lects[0]['origen_id'][1] == 'Estimada'
#                and check_origen(lects, back_idx, "Estimada")) \
            if (check_origen(lects, back_idx, "Estimada")) \
                and (((lects[0]['lectura'] >= lects[last_idx]['lectura'])
                and (lects[0]['lectura'] < lects[prev_idx]['lectura']))
                or ((offset == 2) and
                (lects[1]['lectura'] >= lects[last_idx+1]['lectura'])
                and (lects[1]['lectura'] < lects[prev_idx+1]['lectura']))):

                n_days_02 = (datetime.strptime(lects[0]['name'], '%Y-%m-%d') -
                             datetime.strptime(lects[last_idx]['name'], '%Y-%m-%d')).days

                for day_idx in range(1,back_idx+1):
                    kWh_day = (lects[0]['lectura']-lects[last_idx]['lectura'])/float(n_days_02)
                    kWh_day_db = O.GiscedataPolissa.consum_diari(polissa_id)

                    _prev_idx = offset+(back_idx-day_idx)*offset
                    _last_idx = offset+(back_idx-day_idx+1)*offset
                    n_days_12 = (datetime.strptime(lects[_prev_idx]['name'], '%Y-%m-%d') -
                                 datetime.strptime(lects[_last_idx]['name'], '%Y-%m-%d')).days

                    print '## 02:{n_days_02} 12:{n_days_12} kWh_day:{kWh_day} kWh_day_db:{kWh_day_db[P1]}'.format(**locals())
                    if (kWh_day/kWh_day_db['P1']) > 5:
                        quarantine['kWh'].append(polissa_id)

                    lect_old = lects[_prev_idx]['lectura']
                    lects[_prev_idx]['lectura'] = lects[_last_idx]['lectura']+n_days_12*kWh_day
                    observacions = u'R. {lect_old}\n{observacions}'.format(**{'lect_old':lect_old,
                                                                             'observacions':lects[_prev_idx]['observacions']})
                    O.GiscedataLecturesLectura.write([lects[_prev_idx]['id']],
                                                     {'lectura': lects[_prev_idx]['lectura'],
                                                      'observacions': u'{observacions}'.format(**locals())})

                    if offset == 2:
                        # 2.XDHA

                        kWh_day = (lects[0]['lectura']-lects[last_idx+1]['lectura'])/float(n_days_02)

                        n_days_12 = (datetime.strptime(lects[_prev_idx+1]['name'], '%Y-%m-%d') -
                                     datetime.strptime(lects[_last_idx+1]['name'], '%Y-%m-%d')).days

                        print '## 02:{n_days_02} 12:{n_days_12} kWh_day:{kWh_day} kWh_day_db:{kWh_day_db[P2]}'.format(**locals())
                        if (kWh_day/kWh_day_db['P2']) > 5:
                            quarantine['kWh'].append(polissa_id)

                        lect_old = lects[_prev_idx+1]['lectura']
                        lects[_prev_idx+1]['lectura'] = lects[_last_idx+1]['lectura']+n_days_12*kWh_day
                        observacions = 'R. {lect_old}\n{observacions}'.format(**{'lect_old':lect_old,
                                                                                 'observacions':lects[_prev_idx+1]['observacions']})
                        O.GiscedataLecturesLectura.write([lects[_prev_idx+1]['id']],
                                                         {'lectura': lects[_prev_idx+1]['lectura'],
                                                          'observacions': '{observacions}'.format(**locals())})

                    dump(polissa_id, lects, 'Fixed', 10)
                    invoice_date_end = lects[_prev_idx]['name']
                    invoice_date_start = lects[_last_idx]['name']
                    invoice_rectified_id = O.GiscedataFacturacioFactura.search([('polissa_id', '=', polissa_id),
                                                                                        ('type', '=', 'out_invoice'),
                                                                                        ('data_final', '=', invoice_date_end),
                                                                                        ('data_inici', '=', invoice_date_start)])

                    if not invoice_rectified_id:
                        invoice_date_start = datetime.strftime(datetime.strptime(lects[_last_idx]['name'],
                                                                                 '%Y-%m-%d') + timedelta(days=1), '%Y-%m-%d')
                        invoice_rectified_id = O.GiscedataFacturacioFactura.search([('polissa_id', '=', polissa_id),
                                                                                    ('type', '=', 'out_invoice'),
                                                                                    ('data_final', '=', invoice_date_end),
                                                                                    ('data_inici', '=', invoice_date_start)])

                    if invoice_rectified_id:
                        invoices_id = payInvoice(invoice_rectified_id[0], True)
                        if invoices_id:
                            invoices = O.GiscedataFacturacioFactura.read(invoices_id, ['amount_total'])
                            invoice_original = invoices[1]['amount_total']
                            invoice_rectified = invoices[0]['amount_total']
                            diff = invoice_original - invoice_rectified
                            print 'original: {invoice_original} rectified: {invoice_rectified} diff: {diff}'.format(**locals())

                            if diff > 2*get_contract_amount_mean(polissa_id):
                                quarantine['euro'].append(polissa_id)

        except Exception, e:
            print e
            pass


#lot_error_ids = O.GiscedataFacturacioContracte_lot.search([('status', 'like', 'La lectura actual és inferior')])
#lot_errors = O.GiscedataFacturacioContracte_lot.read(lot_error_ids, ['lot_id', 'polissa_id'])
#
#for lot_error in lot_errors:
#    fix_contract(lot_error['polissa_id'][0])
#fix_contract(30607)
quarantine = {'kWh': [], 'euro': []}
fix_contract(44802, quarantine)
