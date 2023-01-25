#!/usr/bin/env python
# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()

import configdb
from consolemsg import step, error, warn, fail, success
import pymongo


def get_mongo_data(mongo_db, mongo_collection, cups):
    data = dict()
    query = {'name': {'$regex': '^{}'.format(cups[:20])}}
    fields = {'_id': False}
    curves =  mongo_db[mongo_collection].find(
        query,
        fields)
    return curves


def set_mongo_data(mongo_db, mongo_collection, curve_type, cups, mongo_data):
    try:
        result = mongo_db[mongo_collection].insert(
            mongo_data, continue_on_error=True)
    except pymongo.errors.DuplicateKeyError as e:
        print("Alguns registres de la corba " + curve_type + " ja existeixen.")
        print(str(e))
    except Exception as e:
        print("Error no controlat: " + str(e))
        return False
    return True


def main(cups, server):
    mongo_client_prod = pymongo.MongoClient(configdb.mongodb_prod)
    if server == 'terp01':
        mongo_client_test = pymongo.MongoClient(configdb.mongodb_test)
    elif server == 'perp01':
        mongo_client_test = pymongo.MongoClient(configdb.mongodb_pre)
    elif server == 'serp01':
        mongo_client_test = pymongo.MongoClient(configdb.mongodb_serp)
    else:
        raise Exception("Servidor desconegut")

    mongo_db_prod = mongo_client_prod.somenergia
    mongo_db_test = mongo_client_test.somenergia

    curve_types = dict(
        F5D = 'tg_cchfact',
        F1 = 'tg_f1',
        P5D = 'tg_cchval',
        P1 = 'tg_p1',
        TM_PROFILE = 'tm_profile',
        GENNETABETA = 'tg_cch_gennetabeta',
    )
    
    for name, collection in curve_types.items():
        mongo_data = get_mongo_data(
            mongo_db=mongo_db_prod, mongo_collection=collection, cups = cups
        )

        step("Corbes obtingudes {}: {}".format(name, mongo_data.count()))

        if mongo_data.count() > 0:
            result = set_mongo_data(
                mongo_db=mongo_db_test,
                mongo_collection=collection,
                curve_type=name,
                cups=cups,
                mongo_data=mongo_data,
            )

    print("Les corbes disponibles s'han pujat a " + server)

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Copiar corbes a Testing')
    parser.add_argument('-c', '--cups',
        help="CUPS a copiar",
        required=False,
    )
    parser.add_argument('-s', '--server',
        help="Escull un servidor destí",
    )
    return parser.parse_args()

if __name__ == '__main__':
    args=parseargs()
    if not args.cups:
        fail("Introdueix un cups o el missatge d'error o una data")
    if not args.server:
        fail("Introdueix un servidor a on copiar les corbes")

    main(args.cups, args.server)
