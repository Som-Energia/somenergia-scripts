#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configdb
from consolemsg import step, error, warn, fail, success
from datetime import datetime, timedelta
import pymongo
from erppeek import Client
from bson.objectid import ObjectId
from tqdm import tqdm
import argparse


def is_winter_hour_change(dt):

    if dt.month == 10 and dt.hour == 2 and dt.weekday() == 6:
        next_sunday = dt + timedelta(days=7)
        if next_sunday.month != 10:
            return True

    return False

def get_mongo_name_datetime_duplicateds(mongo_db, mongo_collection, cups):
    data = dict()
    name_datetime_duplicateds_query = [
        {'$match': {'name': {'$regex': '^{}'.format(cups[:20])}, 'datetime': {'$gt': datetime(2021,1,1)}}},
        {'$group': {'_id': {'datetime': '$datetime', 'name': '$name'},
            'count': {'$sum': 1},
            'uniqueIds': {'$addToSet': '$_id'}}},
        {'$match': {'count': {'$gt': 1}}}
    ]

    duplicateds =  mongo_db[mongo_collection].aggregate(
        name_datetime_duplicateds_query,
        allowDiskUse=True)
    result = duplicateds['result']

    return result

def treat_duplicateds(mongo_db, mongo_collection, cups, doit=False):
    total_deleted = 0
    for cups_name in cups:
        duplicateds = get_mongo_name_datetime_duplicateds(mongo_db, mongo_collection, cups_name)
        deleted_by_cups = duplicateds_by_cups(duplicateds, mongo_db, mongo_collection, doit)
        total_deleted += deleted_by_cups
        if deleted_by_cups:
            step("Trobats {} duplicats del CUPS {}".format(deleted_by_cups, cups_name))
    success("Eliminats {} registres".format(total_deleted))

def duplicateds_by_cups(duplicateds, mongo_db, mongo_collection, doit=False):
    total_deleted = 0
    count_different_values = 0
    entry_example = False
    for entry in duplicateds:
        try:
            if not 'name' in entry['_id']:
                continue
            to_delete = not is_winter_hour_change(entry['_id']['datetime'])
            if to_delete:
                cr = list(mongo_db[mongo_collection].find({'_id':{'$in': entry['uniqueIds']}}))
                informed_ai = [x['ai'] for x in cr if 'ai' in x]
                if len(informed_ai) != len(cr):
                    warn("Element/s sense ai", cr)
                    continue
                if len(set(informed_ai)) == 1:
                    total_deleted += len(cr)-1
                    if doit:
                        del_res = mongo_db[mongo_collection].delete_many({'_id':{'$in': entry['uniqueIds'][1:]}})
                else:
                    count_different_values += 1
                    entry_example = entry['_id']
                    #warn("Repetits amb diferents valors ai ", cr)
        except KeyboardInterrupt as e:
            break
        except Exception as e:
            error("Error: {}".format(e))
    if count_different_values:
        warn("Trobats {} repetits amb diferents valors, per exemple CUPS {}, diahora {}".format(
            count_different_values, entry_example['name'], entry_example['datetime'])
        )
    return total_deleted

def get_cups_names(erpclient):
    step("Buscant CUPS")
    cups_ids = erpclient.GiscedataCupsPs.search([], context={'active_test': False})
    cups_names = erpclient.GiscedataCupsPs.read(cups_ids, ['name'])
    return [x['name'] for x in cups_names]

def main(doit=False):

    mongo_client = pymongo.MongoClient(**configdb.mongodb)
    mongo_db = mongo_client.somenergia
    erpclient = Client(**configdb.erppeek)
    cups_names = get_cups_names(erpclient)
    step("Trobats {} CUPS".format(len(cups_names)))
    for col in ['tg_cchfact', 'tg_cchval']:
        step("Tractant la coŀlecció {}".format(col))
        treat_duplicateds(mongo_db, col, cups_names, doit)

    if not doit:
        warn("S'ha executat sense el doit: mode consulta")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Elimina registres de cch duplicats"
    )

    parser.add_argument(
        '--doit',
        type=bool,
        default=False,
        const=True,
        nargs='?',
        help='realitza les accions'
    )

    args = parser.parse_args()
    main(doit=args.doit)
