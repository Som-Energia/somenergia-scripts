# -*- coding: utf-8 -*-

import os
import base64
import re

from datetime import datetime
import dateutil.parser
import bisect

from ooop import OOOP
from models import F1ImportError, \
    codigoOrigen_to_O, \
    O_to_codigoOrigen
from errors import IMP_ERRORS

DB_NAME = ''
DB_USER = ''
DB_PASSWORD = ''
DB_URI = ''
DB_PORT = 8069 

START_DATE = '2014-01-01'

O = OOOP(dbname=DB_NAME, user=DB_USER, pwd=DB_PASSWORD, port=int(DB_PORT), uri=DB_URI)
e_search = [('state', '=', 'erroni'),
            ('info', 'like', 'Divergència'),
            ('cups_id', '!=', False),
            ('data_carrega', '>', START_DATE)]
e_ids = O.GiscedataFacturacioImportacioLinia.search(e_search)
fields_to_read = ['cups_id']
e_cups = O.GiscedataFacturacioImportacioLinia.read(e_ids, fields_to_read)
cups_ids = {}
for e in e_cups:
    cups_id = e['cups_id'][0]
    cups_ids.setdefault(cups_id, [])
    bisect.insort(cups_ids[cups_id], e['id'])


def check_is_origen(e, origen):
    if isinstance(origen, list):
        return e.error.lects_pool[e.error.periode].origen in origen
    else:
        return e.error.lects_pool[e.error.periode].origen == origen


def diff_xml_db(e):
    return e.error.valor_xml - e.error.valor_db


def check_is_fixed(e_id):
    search_fields = [('state', '=', 'erroni'),
                     ('info', 'like', 'Divergència'),
                     ('id', '=', e_id)]
    return len(O.GiscedataFacturacioImportacioLinia.search(search_fields)) == 0


def ask_to_continue(message=''):
    input_key = raw_input("{message} (y/n)".format(**locals()))
    return input_key.rstrip().lower() == 'y'


def force_f1_reload(O, e_id):
    ctx = {'active_id': e_id, 'fitxer_xml': True}
    wizard_id = O.GiscedataFacturacioSwitchingWizard.create({}, ctx)
    wizard = O.GiscedataFacturacioSwitchingWizard.get(wizard_id)
    wizard.action_importar_f1(ctx)


N_RETRIES = 3
for cups_id, e_ids in cups_ids.items()[100:]:
    if cups_id in []:
        continue

    print 'cups: %d' % cups_id
    for idx, e_id in enumerate(sorted(e_ids)):
        print 'error: %d' % e_id
        try:
            n_retries = 0

            ongoing = []
            while not check_is_fixed(e_id) and n_retries < N_RETRIES:
                n_retries += 1
                force_f1_reload(O, e_id)
                if check_is_fixed(e_id):
                    break

                if e_id in []:
                    break
                try:
                    e = F1ImportError(O, e_id)
                except Exception, ex:
                    print e_id
                    print ex
                    break

                if (e.polissa.tarifa not in ['2.0A', '2.0DHA', '2.1A', '2.1DHA']) or \
                        (e.error.tipus == 'M'):
                    break

                for imp_cls_name in sorted(IMP_ERRORS):
                    imp_cls = IMP_ERRORS[imp_cls_name]
                    if imp_cls.check(O, e):
                        print '#### {}'.format(imp_cls.description)
                        e.dump()

                        imp_e = imp_cls(O, e)
                        if ask_to_continue('Fix DB measurements ?'):
                            ongoing.append(imp_e)
                            try:
                                imp_e.fix()
                                if imp_e.exit:
                                    break
                            except Exception, ex:
                                print ex

                        if imp_e.exit:
                            break


            for imp_e in ongoing:
                imp_e.done()

            if not check_is_fixed(e_id):
                continue

            for imp_e in ongoing:
                if not imp_e.invoicing:
                    continue

                if not ask_to_continue('Fix invoicing issues ?'):
                    continue

                e = imp_e.e
                last_lect_pool_date = datetime.strptime(e.error.last_lects_pool[e.error.periode].date,'%Y-%m-%d')
                last_lect_pool_measure = e.error.last_lects_pool[e.error.periode].lectura
                last_lect_invoice_date = datetime.strptime(e.error.last_lects_invoice[e.error.periode].date,'%Y-%m-%d')
                last_lect_invoice_measure = e.error.last_lects_invoice[e.error.periode].lectura

                lect_pool_date = datetime.strptime(e.error.data,'%Y-%m-%d')
                if last_lect_pool_date > lect_pool_date and \
                                last_lect_pool_measure > e.error.valor_xml and \
                                last_lect_invoice_date > lect_pool_date and \
                                last_lect_invoice_measure > e.error.valor_xml:
                    print 'INFO: XML measure < BDD measure: Last invoice already fixed'
                else:
                    diff = diff_xml_db(e)
                    monthly_consumption = e.polissa.monthly_consumption(e.error.periode)
                    print 'INFO: diff: {} monthly_consumption {}'.format(abs(diff), monthly_consumption)
                    if diff >= 0:
                        print 'INFO: XML measure > BDD measure: {}'.format(diff)
                        if diff < monthly_consumption:
                            print 'INFO: Fixed in next billing period (diff < monthly mean consumption)'
                        else:
                            print 'WARNING: To be reviewed (diff > monthly mean consumption)'
                        pass
                    else:
                        print 'INFO: XML measure < BDD measure: {}'.format(diff)
                        print 'WARNING: To be reviewed'

                        new_origen = codigoOrigen_to_O[str(e.get_xml_attribute('Procedencia'))]
                        old_origen = e.error.lects_pool[e.error.periode].origen

                        origen_groups = {
                            'Telemedida': 'Real',
                            'Telemedida corregida': 'Real',
                            'TPL': 'Real',
                            'TPL corregida': 'Real',
                            'Visual': 'Real',
                            'Visual corregida': 'Real',
                            'Estimada': 'Estimada',
                            'Autolectura': 'Autolectura',
                            'Sense Lectura': 'Estimada',
                            'Sin Lectura': 'Estimada'
                        }
                        new_origen_group = origen_groups[new_origen]
                        old_origen_group = origen_groups[old_origen]

                        CEFACO_ACTION = {
                            ('Estimada', 'Estimada'): False,
                            ('Autolectura', 'Autolectura'): False,
                            ('Real', 'Real'): False,
                            ('Estimada', 'Autolectura'): False,
                            ('Autolectura', 'Estimada'): True,
                            ('Estimada', 'Real'): False,
                            ('Real', 'Estimada'): False,
                            ('Autolectura', 'Real'): False,
                            ('Real', 'Autolectura'): False
                        }
                        action_id = (old_origen_group, new_origen_group)
                        if action_id not in CEFACO_ACTION.keys():
                            raise 'Scenario not handled {} {}'.format(old_origen_group, new_origen_group)

                        if CEFACO_ACTION[action_id]:
                            print 'WARNING: CEFACO required'

            if ask_to_continue('Show post status ?'):
                e.dump()

        except Exception, ex:
            print ex

