#!/usr/bin/env python
# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()


import configdb
import csv
from consolemsg import step, error, warn, fail, success
from erppeek import Client
from emili import sendMail
import pymongo
from datetime import datetime, timedelta, date, time
from pymongo import DESCENDING


CURVES_SOURCE_TYPES = [1, 2, 3, 4, 5, 6, 7]


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
        md = "Hola, Os fem arribar el csv d'aquesta setmana :)",
        attachments = [attachment],
        config = 'configdb.py',
    )


def create_csv(csv_name, headers):
    with open(csv_name, mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()


def add_row_in_csv(csv_name, header, element):
    with open(csv_name, mode='a+') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header)
        writer.writerow(element)


def get_count(mongo_db, mongo_collection, start_date, end_date, cups, source_type=False):

    queryparms = {
        "name": {'$regex': '^{}'.format(cups[:20])},
        "datetime" : {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    if source_type:
        queryparms.update({"source": {'$eq': source_type}})
    if mongo_collection == 'tg_p1':
        queryparms.update({"type": "p"})
    count_curves = mongo_db[mongo_collection].find(queryparms).count()
    return count_curves


def get_mongo_data(mongo_db, mongo_collection, curve_type, cups, date_F1ATR):
    data = dict()
    all_curves_search_query = {'name': {'$regex': '^{}'.format(cups[:20])}}
    fields = {'_id': False, 'datetime': True, 'create_at': True, 'source': True}
    curves =  mongo_db[mongo_collection].find(
        all_curves_search_query,
        fields).sort('datetime', pymongo.ASCENDING)

    last_year = datetime.combine(date.today(), time()) - timedelta(days=365)
    count_hores_period = (
        datetime.strptime(date_F1ATR,"%Y-%m-%d") - last_year
    ).days * 24.

    if curves.count() > 0:
        source_types = curves.distinct('source')
        if curves[0]['datetime'] < last_year:
            count_curves = get_count(
                mongo_db=mongo_db,
                mongo_collection=mongo_collection,
                start_date=last_year,
                end_date=datetime.strptime(date_F1ATR,"%Y-%m-%d"),
                cups=cups
            )
            data['count_cch_period_{}'.format(curve_type)] = count_curves
            for source_type in source_types:
                data['count_source_type_{source_type}_{curve_type}'.format(
                    source_type=source_type,
                    curve_type=curve_type)] = get_count(
                        mongo_db=mongo_db,
                        mongo_collection=mongo_collection,
                        start_date=last_year,
                        end_date=datetime.strptime(date_F1ATR,"%Y-%m-%d"),
                        cups=cups,
                        source_type=source_type)

        if curves[0]['datetime'] > last_year:
            count_curves = get_count(
                mongo_db=mongo_db,
                mongo_collection=mongo_collection,
                start_date=datetime.strptime(date_F1ATR,"%Y-%m-%d"),
                end_date=curves[0]['datetime'],
                cups=cups
            )
            data['count_cch_period_{}'.format(curve_type)] = count_curves
            for source_type in source_types:
                data['count_source_type_{source_type}_{curve_type}'.format(
                    source_type=source_type,
                    curve_type=curve_type)] = get_count(
                        mongo_db=mongo_db,
                        mongo_collection=mongo_collection,
                        start_date=datetime.strptime(date_F1ATR,"%Y-%m-%d"),
                        end_date=curves[0]['datetime'],
                        cups=cups,
                        source_type=source_type)

        cursor = mongo_db[mongo_collection].find(all_curves_search_query, fields
                ).sort('datetime', pymongo.DESCENDING)
        data['ultima_data_creacio_{}'.format(curve_type)] = cursor[0].get(
            'create_at'
        ).strftime("%Y-%m-%d %H:%M:%S")
        data['data_ultim_registre_{}'.format(curve_type)] = cursor[0].get(
            'datetime'
        ).strftime("%Y-%m-%d %H:%M:%S")
        data['data_primera_{}'.format(curve_type)] = curves[0]['datetime']
        data['count_hores_period_{}'.format(curve_type)] = count_hores_period
        data['count_diferencia_{}'.format(curve_type)] = count_curves - count_hores_period
    return data


def get_polissa(erp_client, polissa_obj):
    filters = [
        ('active', '=', True),
        ('state', '=', 'activa'),
        ('data_baixa', '=', False)
    ]

    return polissa_obj.search(filters)

def get_data_ultima_lectura_F1ATR(erp_client, contractId):
    factura_obj = erp_client.model('giscedata.facturacio.factura')
    filters = [
        ('polissa_state', '=', 'activa'),
        ('type', '=', 'in_invoice'),
        ('polissa_id.name', '=', contractId),
    ]
    _F1ATR = sorted(factura_obj.search(filters))[-1]
    return {
        'data_ultima_lectura_F1ATR': factura_obj.read(_F1ATR)['data_final']
    }

def get_mongo_fields():
    mongo_fields = []

    curve_fields = [
        'data_primera_{curve_type}', 'count_hores_period_{curve_type}',
        'count_cch_period_{curve_type}', 'count_diferencia_{curve_type}',
        'ultima_data_creacio_{curve_type}', 'data_ultim_registre_{curve_type}'
    ]

    for curve_type in ['f5d', 'f1', 'p5d', 'p1', 'auto']:
        mongo_fields = mongo_fields + [
            curve_field.format(curve_type=curve_type) for curve_field in curve_fields
        ]
        mongo_fields = mongo_fields + [
            'count_source_type_{source_type}_{curve_type}'.format(
                source_type=source_type, curve_type=curve_type
            ) for source_type in CURVES_SOURCE_TYPES
        ]
    return mongo_fields


def main():
    erp_client = Client(**configdb.erppeek)
    mongo_client = pymongo.MongoClient(configdb.mongodb)
    mongo_db = mongo_client.somenergia
    polissa_obj = erp_client.model('giscedata.polissa')

    today = datetime.today().date()

    erp_fields = [
        'tg', 'distribuidora', 'autoconsumo', 'cups', 'data_alta',
        'data_ultima_lectura', 'tarifa', 'name',
        'data_ultima_lectura_estimada', 'data_ultima_lectura_perfilada',
    ]

    mongo_fields = get_mongo_fields()
    csv_name = 'curves_info_{}.csv'.format(datetime.now().strftime("%Y-%m-%d"))
    csv_fields = erp_fields + ['data_ultima_lectura_F1ATR', 'data_avui'] + mongo_fields
    step('creating csv...')
    create_csv(csv_name, csv_fields)
    step('Getting polissa data')
    polissas = get_polissa(erp_client, polissa_obj)

    step('Getting CCHs')
    for polissa_id in polissas:
        polissa = polissa_obj.read(polissa_id, erp_fields)
        cleared_polissa = {
            key:value if value.__class__ != list else value[1].encode('utf-8')
            for key,value in polissa.items()
        }
        cleared_polissa['cups'] = cleared_polissa['cups'][:6]


        cleared_polissa['data_avui'] = today
        lectura_F1ATR = get_data_ultima_lectura_F1ATR(
            erp_client, polissa['name']
        )
        del cleared_polissa['id']

        if bool(lectura_F1ATR) and bool(lectura_F1ATR['data_ultima_lectura_F1ATR']):
            cleared_polissa.update(lectura_F1ATR)
            mongo_data_f5d = get_mongo_data(
                mongo_db=mongo_db, mongo_collection='tg_cchfact',
                curve_type='f5d', cups=polissa['cups'][1],
                date_F1ATR=lectura_F1ATR['data_ultima_lectura_F1ATR']
            )
            mongo_data_f1 = get_mongo_data(
                mongo_db=mongo_db, mongo_collection='tg_f1',
                curve_type='f1', cups=polissa['cups'][1],
                date_F1ATR=lectura_F1ATR['data_ultima_lectura_F1ATR']
            )
            mongo_data_p5d = get_mongo_data(
                mongo_db=mongo_db, mongo_collection='tg_cchval',
                curve_type='p5d', cups=polissa['cups'][1],
                date_F1ATR=lectura_F1ATR['data_ultima_lectura_F1ATR']
            )
            mongo_data_p1 = get_mongo_data(
                mongo_db=mongo_db, mongo_collection='tg_p1',
                curve_type='p1', cups=polissa['cups'][1],
                date_F1ATR=lectura_F1ATR['data_ultima_lectura_F1ATR']
            )
            mongo_data_auto = get_mongo_data(
                mongo_db=mongo_db, mongo_collection='tg_cch_autocons',
                curve_type='auto', cups=polissa['cups'][1],
                date_F1ATR=lectura_F1ATR['data_ultima_lectura_F1ATR']
            )
            cleared_polissa.update(mongo_data_f5d)
            cleared_polissa.update(mongo_data_f1)
            cleared_polissa.update(mongo_data_p5d)
            cleared_polissa.update(mongo_data_p1)
            cleared_polissa.update(mongo_data_auto)
            add_row_in_csv(csv_name, header=csv_fields, element=cleared_polissa)
    step('ready to send the email')
    sendmail2all(configdb.user, csv_name)


if __name__ == '__main__':
    main()
