# -*- coding: utf-8 -*-
import sys
import os
import signal
from datetime import datetime, timedelta

import configdb

from ooop import OOOP
from consolemsg import error
from utils import load_new_measures, get_measures_by_contract, get_contract_status
from validation_utils import adelantar_polissa_endarerida


def remove_modmeter_lect(meters, lects):
    dates_out = {meter['data_baixa']: meter['id'] for meter in meters if meter['data_baixa']}
    return [lect for lect in lects if not((lect['name'] in dates_out.keys())
            and not(dates_out[lect['name']] == lect['comptador'][0]))]


def fix_measure(O, polissa_id, lects, last_idx, _last_idx, _prev_idx, offset, kWh_day_db, n_days_02):
    quarantine = []
    kWh_day = (lects[offset]['lectura']-lects[last_idx+offset]['lectura'])/float(n_days_02)

    n_days_12 = (datetime.strptime(lects[_prev_idx+offset]['name'], '%Y-%m-%d') -
                 datetime.strptime(lects[_last_idx+offset]['name'], '%Y-%m-%d')).days

    if ((kWh_day_db == 0) and not(kWh_day == 0)) \
        or (not(kWh_day_db == 0) and ((kWh_day/kWh_day_db) > 5)):
        quarantine.append(polissa_id)

    lect_old = lects[_prev_idx+offset]['lectura']
    lects[_prev_idx+offset]['lectura'] = lects[_last_idx+offset]['lectura']+n_days_12*kWh_day
    observacions = 'R. {lect_old}\n{observacions}'.format(**{'lect_old':lect_old,
                                                             'observacions':lects[_prev_idx+offset]['observacions']})

    measures_id = [lects[_prev_idx+offset]['id']]
    measures_value = {'lectura': lects[_prev_idx+offset]['lectura'],
                      'observacions': '{observacions}'.format(**locals())}
    update_measures(O, measures_id, measures_value, pool=False)

    return quarantine


def fix_contract(O, polissa_id, quarantine, start_date=None, end_date=None):
    out = ''
    fields_to_search = [('polissa', '=', polissa_id)]
    fields_to_read = ['active', 'data_alta', 'data_baixa']
    meters = get_meters(O, fields_to_search, fields_to_read, False)

    if not isinstance(meters, list):
        meters = [meters]

    for meter in meters:
        fields_to_search = [('comptador', '=', meter['id'])]
        if start_date:
            fields_to_search.append(('name', '>=', start_date))
        if end_date:
            fields_to_search.append(('name', '<=', end_date))

        fields_to_read = ['name', 'comptador', 'periode', 'lectura', 'origen_id', 'observacions']
        lects = get_measures(O, fields_to_search, fields_to_read, pool=False, active_test=False)
        #lects = remove_modmeter_lect(meters, lects)
        out += show_invoice(polissa_id, lects, None, 10)

        if len(lects) < 2:
            return

        offset_ct = {'2.0A (P1)': 1, '2.1A (P1)': 1,
                     '2.0DHA (P1)': 2, '2.1DHA (P1)': 2}

        for back_idx in reversed(range(1, min(len(lects), 15))):
            if not (lects[0]['periode'][1].startswith('2')) or (lects[0]['periode'][1].endswith('DHS')):
                # 3.0 and DHS pending
                continue

            offset = offset_ct[lects[0]['periode'][1]]
            try:
                def check_origen(lects, n, origen, start, offset):
                    for idx in range(start, n+1, offset):
                        if not lects[idx]['origen_id'][1] == origen:
                            return False
                    return True

                prev_idx = back_idx*offset
                last_idx = offset + prev_idx

                offset_status = [check_origen(lects, prev_idx, "Estimada", offset, offset),
                                 check_origen(lects, prev_idx, "Estimada", offset+1, offset)]

                if ((offset_status[0]) \
                    and (lects[0]['lectura'] >= lects[last_idx]['lectura']) \
                    and (lects[0]['lectura'] < lects[prev_idx]['lectura'])) \
                    or ((offset == 2) \
                    and (offset_status[1]) \
                    and (lects[1]['lectura'] >= lects[last_idx+1]['lectura']) \
                    and (lects[1]['lectura'] < lects[prev_idx+1]['lectura'])):

                    n_days_02 = (datetime.strptime(lects[0]['name'], '%Y-%m-%d') -
                                 datetime.strptime(lects[last_idx]['name'], '%Y-%m-%d')).days

                    for day_idx in range(1, back_idx+1):
                        _prev_idx = offset+(back_idx-day_idx)*offset
                        _last_idx = offset+(back_idx-day_idx+1)*offset
                        kWh_day_db = get_contract_daily_consumption(O, polissa_id)

                        if offset_status[0]:
                            # 2.XA
                            quarantine['kWh'] += fix_measure(O, polissa_id, lects, last_idx, _last_idx, _prev_idx,
                                                             0, kWh_day_db['P1'], n_days_02)

                        if offset == 2 and offset_status[1]:
                            # 2.XDHA
                            quarantine['kWh'] += fix_measure(O, polissa_id, lects, last_idx, _last_idx, _prev_idx,
                                                             1, kWh_day_db['P2'], n_days_02)


                        out += show_invoice(polissa_id, lects, 'Fixed', 10)
                        invoice_date_end = lects[_prev_idx]['name']
                        invoice_date_start = lects[_last_idx]['name']
                        search_pattern = [('polissa_id', '=', polissa_id),
                                          ('type', '=', 'out_invoice'),
                                          ('data_final', '=', invoice_date_end),
                                          ('data_inici', '=', invoice_date_start)]
                        invoice_rectified_id = get_invoices(O, search_pattern, None, True)

                        if not invoice_rectified_id:
                            invoice_date_start = datetime.strftime(datetime.strptime(lects[_last_idx]['name'],
                                                                                     '%Y-%m-%d') + timedelta(days=1), '%Y-%m-%d')
                            search_pattern = [('polissa_id', '=', polissa_id),
                                              ('type', '=', 'out_invoice'),
                                              ('data_final', '=', invoice_date_end),
                                              ('data_inici', '=', invoice_date_start)]
                            invoice_rectified_id = get_invoices(O, search_pattern, None, True)

                        if invoice_rectified_id:
                            invoices_id = pay_invoice(O, invoice_rectified_id[0], True)
                            if invoices_id:
                                fields_to_read= ['invoice_id',
                                                 'data_inici',
                                                 'data_final',
                                                 'amount_total']
                                invoices = read_invoices(O, invoices_id, fields_to_read)
                                invoice_original = invoices[1]['amount_total']
                                invoice_rectified = invoices[0]['amount_total']
                                diff = invoice_original - invoice_rectified

                                if diff > 2*get_contract_amount_mean(O, polissa_id):
                                    quarantine['euro'].append(polissa_id)

                                out += show_results(invoices, quarantine)

            except Exception, e:
                print e
                pass
    return out


def signal_handler(signal, frame):
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Refund and rectify invoice')
    parser.add_argument('-s', '--startdate')
    parser.add_argument('-e', '--enddate')
    parser.add_argument('-c','--contractname',required=True)
    args = vars(parser.parse_args())
    start_date = args['startdate']
    end_date = args['enddate']
    contract_name = args['contractname']
    def valid_date(date_text):
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return True


    O = None
    try:
        O = OOOP(**configdb.ooop)
    except:
        error("Unable to connect to ERP")
        raise

    if not contract_name:
        error("Contracte name missing")
        raise

    start_date = start_date if start_date and valid_date(start_date) else None

    end_date = end_date if end_date and valid_date(end_date) else None

    contract_id = O.GiscedataPolissa.search([('name', '=', contract_name)])[0]
    quarantine = {'kWh': [], 'euro': []}

    old_measures = get_measures_by_contract(O, contract_id, range(1,12))
    new_measures = load_new_measures(O, contract_id)
    if old_measures[0]['origen_id'][0] not in [7,10,11]:
        end_date = old_measures[0]['name']
    else:
        if new_measures:
            end_date = new_measures[-1]['name']
    out += fix_contract(O, contract_id, quarantine, start_date, end_date)
    adelantar_polissa_endarerida(O, [contract_id])
    print out
