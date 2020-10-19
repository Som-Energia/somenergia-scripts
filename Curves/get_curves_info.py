import configdb
import csv
from erppeek import Client
import pymongo
from datetime import datetime
from pymongo import DESCENDING


CURVES_SOURCE_TYPES = [1, 2, 3, 4, 5, 6]


def create_csv(csv_name, headers):
    with open(csv_name, mode='w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()


def add_row_in_csv(csv_name, header, element):
    with open(csv_name, mode='a+') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header)
        writer.writerow(element)


def get_mongo_data(mongo_db, mongo_collection, curve_type, cups):
    data = dict()
    all_curves_search_query = {'name': {'$regex': '^{}'.format(cups[:20])}}
    this_year_curves_search_query = {
        'name': {'$regex': '^{}'.format(cups[:20])},
        'datetime': {'$gte': datetime(datetime.now().year, 1, 1)}
    }
    count_all_curves = mongo_db[mongo_collection].count_documents(
        filter=all_curves_search_query
    )
    data['count_{}'.format(curve_type)] = count_all_curves
    data['count_any_actual_{}'.format(curve_type)] = mongo_db[mongo_collection].count_documents(
        filter=this_year_curves_search_query
    )
    cursor = mongo_db[mongo_collection].find(
        all_curves_search_query,
        {'_id': False, 'datetime': True, 'create_at': True, 'source': True}
    ).sort('datetime', DESCENDING)
    if count_all_curves > 0:
        cursor = mongo_db[mongo_collection].find(
            all_curves_search_query,
            {'_id': False, 'datetime': True, 'create_at': True, 'source': True}
        ).sort('datetime', DESCENDING)
        data['ultima_data_creacio_{}'.format(curve_type)] = cursor[0].get(
            'create_at'
        ).strftime("%Y-%m-%d %H:%M:%S")
        data['data_ultim_registre_{}'.format(curve_type)] = cursor[0].get(
            'datetime'
        ).strftime("%Y-%m-%d %H:%M:%S")
        source_types = cursor.distinct('source')
        for source_type in CURVES_SOURCE_TYPES:
            if source_type in source_types:
                data['count_source_type_{source_type}_{curve_type}'.format(
                    source_type=source_type,
                    curve_type=curve_type
                )] = mongo_db[mongo_collection].count_documents(
                    filter={
                        'name': {'$regex':'^{}'.format(cups[:20])},
                        'source': {'$eq': source_type}}
                    )

    return data


def main():
    client = Client(**configdb.erppeek)
    mongo_client = pymongo.MongoClient(configdb.mongodb)
    mongo_db = mongo_client.somenergia
    polissa_obj = client.model('giscedata.polissa')

    filters = [
        ('active', '=', True),
        ('state', '=', 'activa'),
        ('data_baixa', '=', False)
    ]
    erp_fields = [
        'tg', 'distribuidora', 'cups', 'autoconsumo', 'data_alta',
        'data_ultima_lectura', 'tarifa', 'name',
        'data_ultima_lectura_estimada', 'data_ultima_lectura_perfilada',
    ]
    curve_fields = [
        'count_any_actual_{curve_type}', 'count_{curve_type}',
        'ultima_data_creacio_{curve_type}', 'data_ultim_registre_{curve_type}'
    ]
    mongo_fields = []
    for curve_type in ['f5d', 'f1']:
        mongo_fields = mongo_fields + [
            curve_field.format(curve_type=curve_type) for curve_field in curve_fields
        ]
        mongo_fields = mongo_fields + [
            'count_source_type_{source_type}_{curve_type}'.format(
                source_type=source_type, curve_type=curve_type
            ) for source_type in CURVES_SOURCE_TYPES
        ]

    polissas = polissa_obj.search(filters)
    csv_name = 'curves_info_{}.csv'.format(datetime.now().strftime("%Y-%m-%d"))
    create_csv(csv_name, erp_fields + mongo_fields)

    for polissa_id in polissas:
        polissa = polissa_obj.read(polissa_id, erp_fields)
        cleared_polissa = {
            key:value if value.__class__ != list else value[1]
            for key,value in polissa.items()
        }
        del cleared_polissa['id']
        mongo_data = get_mongo_data(
            mongo_db=mongo_db, mongo_collection='tg_cchfact',
            curve_type='f5d', cups=cleared_polissa.get('cups')
        )
        cleared_polissa.update(mongo_data)
        add_row_in_csv(
            csv_name, header=erp_fields + mongo_fields,
            element=cleared_polissa
        )

if __name__ == '__main__':
    main()
