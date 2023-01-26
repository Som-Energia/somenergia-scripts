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

    mongo_data_f5d = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_cchfact', cups = cups
    )
    mongo_data_f1 = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_f1', cups = cups
    )
    mongo_data_p5d = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_cchval', cups = cups
    )
    mongo_data_p1 = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tg_p1', cups = cups
    )
    mongo_data_tmprofile = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='tm_profile', cups = cups
    )


    print("Corbes obtingudes F5D: " + str(mongo_data_f5d.count()))
    print("Corbes obtingudes P5D: " + str(mongo_data_p5d.count()))
    print("Corbes obtingudes F1: " + str(mongo_data_f1.count()))
    print("Corbes obtingudes P1: " + str(mongo_data_p1.count()))


    if mongo_data_f5d.count() > 0:
        result_f5d = set_mongo_data(
            mongo_db=mongo_db_test, mongo_collection='tg_cchfact',
            curve_type='F5D', cups=cups, mongo_data=mongo_data_f5d
        )
    if mongo_data_p5d.count() > 0:
        result_p5d = set_mongo_data(
            mongo_db=mongo_db_test, mongo_collection='tg_cchval',
            curve_type='P5D', cups=cups, mongo_data=mongo_data_p5d
        )
    if mongo_data_f1.count() > 0:
        result_f1 = set_mongo_data(
            mongo_db=mongo_db_test, mongo_collection='tg_f1',
            curve_type='F1', cups=cups, mongo_data=mongo_data_f1
        )
    if mongo_data_p1.count() > 0:
        result_p1 = set_mongo_data(
            mongo_db=mongo_db_test, mongo_collection='tg_p1',
            curve_type='P1', cups=cups, mongo_data=mongo_data_p1
        )
    if mongo_data_tmprofile.count() > 0:
        result_tmprofile = set_mongo_data(
            mongo_db=mongo_db_test, mongo_collection='tm_profile',
            curve_type='TM_PROFILE', cups=cups, mongo_data=mongo_data_tmprofile
        )
        print("Corbes obtingudes TM_PROFILE: " + str(mongo_data_tmprofile.count()))

    print("Les corbes disponibles s'han pujat a " + server)

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Copiar corbes a Testing')
    parser.add_argument('-c', '--cups',
        help="Escull per cups",
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
