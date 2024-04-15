#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from consolemsg import step, success
from datetime import datetime, timedelta

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


# Objectes
pol_obj = O.GiscedataPolissa
lot_obj = O.GiscedataFacturacioLot


open_lot_id = lot_obj.search([('state', '=', 'obert')])[0]
next_lot_id = open_lot_id + 1


def today_minus_days(days):
    days_ago = datetime.today() - timedelta(days=days)
    return datetime.strftime(days_ago, "%Y-%m-%d")


today_minus_1_year = today_minus_days(365)


def polissa_is_old(data):
    if data['state'] != 'baixa':
        return False
    return data['data_baixa'] < today_minus_1_year


def polissa_should_have_lot(data):
    if data['state'] == 'activa':
        if data['facturacio_suspesa']:
            return False
        return True

    if data['state'] == 'baixa':
        if data['facturacio_suspesa']:
            return False

        if data['refacturacio_pendent']:
            return False

        if data['data_alta'] == data['data_baixa']:
            return False

        if data['data_ultima_lectura'] < data['data_baixa']:
            return True

        if data['data_ultima_lectura'] == data['data_baixa']:
            return False

        if data['data_baixa'] <= data['data_ultima_lectura_f1']:
            return False

        return True

    return False


def get_polissa_lot(data):
    if 'lot_facturacio' not in data or data['lot_facturacio'] is False:
        return False, 0
    return True, data['lot_facturacio'][0]


def is_valid_lot(lot_id):
    return lot_id == open_lot_id or lot_id == next_lot_id


def append(storage, key, index):
    if key not in storage:
        storage[key] = [index]
    else:
        storage[key].append(index)


def do_the_thing():
    polissa = {}

    domain = [('state', 'in', ['activa', 'baixa'])]
    ctxt = {"active_test": False}
    step("cercant totes les polisses {}", domain)
    pol_ids = pol_obj.search(domain, context=ctxt)

    fields = [
        'state',
        'data_alta',
        'data_baixa',
        'facturacio_suspesa',
        'data_ultima_lectura_f1',
        'data_ultima_lectura',
        'lot_facturacio',
        'refacturacio_pendent',
        'name'
    ]
    step("llegint totes les polisses {}", len(pol_ids))
    pol_datas = pol_obj.read(pol_ids, fields)
    for pol_data in pol_datas:
        if polissa_is_old(pol_data):
            append(polissa, 'baixa antigues', pol_data)
        else:
            should_have_lot = polissa_should_have_lot(pol_data)
            has_lot, lot_id = get_polissa_lot(pol_data)

            if should_have_lot:
                if has_lot:
                    if is_valid_lot(lot_id):
                        append(polissa, 'lot i ok', pol_data)
                    else:
                        append(polissa, 'lot incorrecte', pol_data)
                else:
                    key = 'hauria de tenir lot pero no, estat ' + pol_data['state']
                    append(polissa, key, pol_data)
            else:
                if has_lot:
                    key = 'lot pero no hauria, estat ' + pol_data['state']
                    append(polissa, key, pol_data)
                else:
                    append(polissa, 'sense lot i ok', pol_data)

    return polissa


def report(res):
    long = max([len(x) for x in res.keys()])
    success("resultats:")
    for k in sorted(res.keys()):
        step("{}{}{}--> {} ", k, ' ', '-' * (long-len(k)), len(res[k]))
        if 'hauria' in k:
            pols = res[k]
            pols = sorted(pols, key=lambda d: d['data_baixa'], reverse=True)
            pols = pols[:20]
            step('  - {}', ', '.join([p['name'] for p in pols]))


if __name__ == '__main__':
    res = do_the_thing()
    report(res)

# vim: et ts=4 sw=4
