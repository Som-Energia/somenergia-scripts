#!/usr/bin/env python
# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()

import os
import configdb
import csv
import tarfile
from consolemsg import step, error, warn, fail, success
from erppeek import Client
from emili import sendMail
import pymongo
from datetime import datetime, timedelta, date, time
from pymongo import DESCENDING
import argparse
from gestionatr.defs import TABLA_17

from tqdm import tqdm
from time import sleep

def sendmail2all(user, attachment):
    '''
    Sends csv by email
    '''
    warn('User info: {}'.format(user))
    sendMail(
        sender = user['sender'],
        to =  user['recipients'],
        bcc = user['bcc'],
        subject = "[Analisi Indexada] Disponibilitat Corbes ",
        md = "Hola, Us fem arribar el csv d'aquesta setmana :)",
        attachments = [attachment],
        config = 'configdb.py',
    )

def make_tarfile(output_filename, source_filename):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_filename, arcname=os.path.basename(source_filename))

def create_csv(csv_name, headers):
    with open(csv_name, mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()


def add_row_in_csv(csv_name, header, element):
    with open(csv_name, mode='a+') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header)
        writer.writerow(element)


def get_count_and_date_firmeza(mongo_db, mongo_collection, cups, firmeza, date):
    queryparms = {
        "name": {'$regex': '^{}'.format(cups[:20])},
        "validated" : firmeza,
        "datetime" : {
            "$gte": date,
        }
    }
    cursor = mongo_db[mongo_collection].find(queryparms)
    count_curves = cursor.count()
    data_ultima = ''
    if count_curves > 0:
        data_ultima = cursor[0]['datetime']
    return count_curves, data_ultima

def get_mongo_data(mongo_db, mongo_collection, curve_type, cups, from_date=None):
    data = dict()
    if from_date:
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
    else:
        from_date = datetime.combine(date.today(), time()) - timedelta(days=365)
    all_curves_search_query = {
        'name': {'$regex': '^{}'.format(cups[:20])},
        'datetime': {"$gte": from_date},
    }
    if mongo_collection == 'tg_p1':
        all_curves_search_query.update({"type": "p"})
    fields = {'_id': False, 'datetime': True, 'create_at': True, 'source': True, 'ai': True, 'ao': True}
    curves =  mongo_db[mongo_collection].find(
        all_curves_search_query,
        fields).sort('datetime', pymongo.ASCENDING)
    number_curves = curves.count()
    data['count_cch_period_{}'.format(curve_type)] = number_curves

    if number_curves > 0:
        sum_ai = 0
        sum_ao = 0
        for curve in curves:
            sum_ai += curve['ai']
            sum_ao += curve['ao']
        curves.rewind()
        data_primera = curves.next()['datetime']
        data['data_primera_{}'.format(curve_type)] = data_primera.strftime("%Y-%m-%d %H:%M:%S")
        curves.rewind()
        curve = curves.skip(number_curves -1).next()
        data['ultima_data_creacio_{}'.format(curve_type)] = curve.get(
            'create_at'
        ).strftime("%Y-%m-%d %H:%M:%S")
        data_ultima = curve.get('datetime')
        data['data_ultim_registre_{}'.format(curve_type)] = data_ultima.strftime("%Y-%m-%d %H:%M:%S")
        count_hores_period = (data_ultima - data_primera).days * 24
        data['count_diferencia_{}'.format(curve_type)] = number_curves - count_hores_period
        data['count_hores_period_{}'.format(curve_type)] = count_hores_period
        data['ai_{}'.format(curve_type)] = sum_ai
        data['ao_{}'.format(curve_type)] = sum_ao

        data['corbes_no_firmes_{}'.format(curve_type)], data['data_ultima_corbes_no_firmes_{}'.format(curve_type)] = get_count_and_date_firmeza(
                mongo_db=mongo_db,
                mongo_collection=mongo_collection,
                firmeza = False,
                cups=cups,
                date=from_date,
        )
        data['corbes_firmes_{}'.format(curve_type)] = number_curves - data['corbes_no_firmes_{}'.format(curve_type)]

    return data


def get_polissa(erp_client, polissa_obj, tariff):
    filters = [
        ('active', '=', True),
        ('state', '=', 'activa'),
        ('data_baixa', '=', False)
    ]

    if tariff:
        filters.append(('tarifa.name', '=', tariff))

    return polissa_obj.search(filters)

def get_mongo_fields():
    mongo_fields = []

    curve_fields = [
        'data_primera_{curve_type}', 'count_hores_period_{curve_type}',
        'count_cch_period_{curve_type}', 'count_diferencia_{curve_type}',
        'ultima_data_creacio_{curve_type}', 'data_ultim_registre_{curve_type}',
        'corbes_firmes_{curve_type}', 'corbes_no_firmes_{curve_type}',
        'data_ultima_corbes_no_firmes_{curve_type}', 'ai_{curve_type}', 'ao_{curve_type}'
    ]

    for curve_type in ['f5d', 'f1', 'p5d', 'p1']:
        mongo_fields = mongo_fields + [
            curve_field.format(curve_type=curve_type) for curve_field in curve_fields
        ]

    return mongo_fields


def main(from_date, tariff):
    erp_client = Client(**configdb.erppeek)
    mongo_client = pymongo.MongoClient(configdb.mongodb)
    mongo_db = mongo_client.somenergia
    polissa_obj = erp_client.model('giscedata.polissa')

    today = datetime.today().date()

    erp_fields = [
        'tg', 'distribuidora', 'autoconsumo', 'cups', 'data_alta',
        'data_ultima_lectura', 'tarifa', 'name',
        'data_ultima_lectura_estimada',
        'data_ultima_lectura_f1', 'tipo_medida',
    ]

    mongo_fields = get_mongo_fields()
    csv_name = 'curves_info_{}.csv'.format(datetime.now().strftime("%Y-%m-%d"))
    csv_fields = erp_fields + ['data_ultima_lectura_factura_real', 'data_avui'] + mongo_fields
    csv_fields.remove('data_ultima_lectura')
    step('creating csv...')
    create_csv(csv_name, csv_fields)
    step('Getting polissa data')
    polissas = get_polissa(erp_client, polissa_obj, tariff)

    step('Getting CCHs')
    for polissa_id in tqdm(polissas):
        try:
            polissa = polissa_obj.read(polissa_id, erp_fields)
            cleared_polissa = {
                key:value if value.__class__ != list else value[1].encode('utf-8')
                for key,value in polissa.items()
            }
            cleared_polissa['cups'] = cleared_polissa['cups'][:6]

            cleared_polissa['data_avui'] = today

            lectura_F1ATR = polissa['data_ultima_lectura_f1']
            cleared_polissa['data_ultima_lectura_factura_real'] = cleared_polissa['data_ultima_lectura']
            del cleared_polissa['id']
            del cleared_polissa['data_ultima_lectura']

            if bool(lectura_F1ATR):
                mongo_data_f5d = get_mongo_data(
                    mongo_db=mongo_db, mongo_collection='tg_cchfact',
                    curve_type='f5d', cups=polissa['cups'][1],
                    from_date=from_date,
                )
                mongo_data_f1 = get_mongo_data(
                    mongo_db=mongo_db, mongo_collection='tg_f1',
                    curve_type='f1', cups=polissa['cups'][1],
                    from_date=from_date,
                )
                mongo_data_p5d = get_mongo_data(
                    mongo_db=mongo_db, mongo_collection='tg_cchval',
                    curve_type='p5d', cups=polissa['cups'][1],
                    from_date=from_date,
                )
                mongo_data_p1 = get_mongo_data(
                    mongo_db=mongo_db, mongo_collection='tg_p1',
                    curve_type='p1', cups=polissa['cups'][1],
                    from_date=from_date,
                )

                cleared_polissa.update(mongo_data_f5d)
                cleared_polissa.update(mongo_data_f1)
                cleared_polissa.update(mongo_data_p5d)
                cleared_polissa.update(mongo_data_p1)
                add_row_in_csv(csv_name, header=csv_fields, element=cleared_polissa)
        except Exception as e:
            print("Error a la polissa amb id {}: {}".format(polissa_id, e))
        sleep(0.1)

    step('ready to send the email')
    tar_filename = 'curves_molonguis_{}.tar.gz'.format(datetime.now().strftime("%Y-%m-%d"))
    make_tarfile(tar_filename, csv_name)
    sendmail2all(configdb.user, tar_filename)

def valid_tariff(tariff):
    tariff_name = None

    if tariff:
        tariff_dict = dict(TABLA_17)
        for key, value in tariff_dict.items():
            if value == tariff:
                tariff_name = value

        if not tariff_name:
            msg = "La tarifa {} no es vàlida".format(tariff)
            raise argparse.ArgumentTypeError(msg)
    return tariff_name

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Script curves molonguis'
    )

    parser.add_argument(
        '--from_date',
        dest='from_date',
        required=False,
        help="Introdueix la data d'inici del perídode que cal decarregar 'YYYY-mm-dd'. Si no es posa res, agafa els últims 365 dies."
    )
    parser.add_argument(
        '--tariff',
        dest='tariff',
        required=False,
        type=valid_tariff,
        help="Introdueix una tarifa (ex. 2.0TD). Si no es posa res, la tarifa no es tinguda en compte."
    )

    args = parser.parse_args()

    main(args.from_date, args.tariff)
