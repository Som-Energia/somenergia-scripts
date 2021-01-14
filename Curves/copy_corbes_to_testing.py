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




def get_mongo_data(mongo_db, mongo_collection, curve_type, cups):
    data = dict()
    all_curves_search_query = {'name': {'$regex': '^{}'.format(cups[:20])}}
    fields = {'_id': False, 'datetime': True, 'create_at': True, 'source': True}
    curves =  mongo_db[mongo_collection].find(
        all_curves_search_query,
        fields)
    return curves



def get_mongo_fields():
    mongo_fields = []

    curve_fields = [
        'data_primera_{curve_type}', 'count_hores_period_{curve_type}',
        'count_cch_period_{curve_type}', 'count_diferencia_{curve_type}',
        'ultima_data_creacio_{curve_type}', 'data_ultim_registre_{curve_type}'
    ]

    for curve_type in ['f5d', 'f1', 'p5d', 'p1']:
        mongo_fields = mongo_fields + [


    return mongo_fields

def set_mongo_data(mongo_db, mongo_collection, curve_type, cups, mongo_data_f5d):
    try:
        curves =  mongo_db[mongo_collection].insert(
            mongo_data_f5d)
    except:
        print "La corba ja existeix"
        return False
    return True

def main():
    mongo_client_prod = pymongo.MongoClient(configdb.mongodb)
    mongo_client_test = pymongo.MongoClient(configdb.mongodb_test)
    mongo_db_prod = mongo_client_prod.somenergia
    mongo_db_test = mongo_client_test.somenergia

    mongo_fields = get_mongo_fields()
    mongo_data_f5d = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_cchfact',
        curve_type='f5d', cups
    )
    mongo_data_f1 = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_f1',
        curve_type='f1', cups
    )
    mongo_data_p5d = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_cchval',
        curve_type='p5d', cups
    )
    mongo_data_p1 = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_p1',
        curve_type='p1', cups
    )

    print "Corbes obtingudes"

    result = set_mongo_data(
        mongo_db=mongo_db_test, mongo_collection='tg_cchfact',
        curve_type='f5d', cups, mongo_data_f5d
    )
    print result


if __name__ == '__main__':
    main()
