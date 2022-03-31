#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configdb
from consolemsg import step, error, warn, fail, success
import pymongo
from bson.objectid import ObjectId
from tqdm import tqdm

def is_winter_hour_change(dt):

    if dt.month == 10 and dt.hour == 2 and dt.weekday() == 6:
        next_sunday = dt + timedelta(days=7)
        if next_sunday.month != 10:
            return True

    return False

def get_mongo_name_datetime_duplicateds(mongo_db, mongo_collection):
    data = dict()
    name_datetime_duplicateds_query = [
        {'$group': {'_id': {'datetime': '$datetime', 'name': '$name'},
            'count': {'$sum': 1},
            'uniqueIds': {'$addToSet': '$_id'}}},
        {'$match': {'count': {'$gt': 1}}}
    ]

    duplicateds =  mongo_db[mongo_collection].aggregate(
        name_datetime_duplicateds_query,
        allowDiskUse=True)
    result = duplicateds['result']
    success("Trobats {} registres duplicats".format(result))
    return result

def treat_duplicateds(mongo_db, mongo_collection, doit=False):
    total_deleted = 0
    duplicateds = get_mongo_name_datetime_duplicateds(mongo_db, mongo_collection)
    for entry in tqdm(duplicateds):
        try:
            if not 'name' in entry['_id'] or 'ai' not in entry['_id']:
                continue
            to_delete = not is_winter_hour_change(entry['_id']['datetime'])
            if to_delete:
                cr = list(mongo_db[mongo_collection].find({'_id':{'$in': entry['uniqueIds']}}))
                informed_ai = [x['ai'] for x in cr if 'ai' in x]
                if len(informed_ai) != len(cr):
                    warn("Element/s sense ai", cr)
                    continue
                if len(set(informed_ai)) == 1:
                    total_deleted + = len(cr)-1
                    if doit:
                        del_res = mongo_db[mongo_collection].delete_many({'_id':{'$in': entry['uniqueIds'][1:]}})
                else:
                    warn("Repetits diferents ", cr)
        except KeyboardInterrupt as e:
            break
        except Exception as e:
            error("Error: {}".format(e))
    success("Eliminats {} registres".format(total_deleted))

def main():

    mongo_client = pymongo.MongoClient(configdb.mongodb)
    mongo_db = mongo_client_prod.somenergia
    for col in ['tg_cchfact', 'tg_cchval']:
        step("Tractant la coŀlecció {}".format(col))
        treat_duplicateds(mongo_db, col)


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
