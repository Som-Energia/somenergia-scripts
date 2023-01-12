#!/usr/bin/env python
# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()

import configdb
from consolemsg import step, error, warn, fail, success
import pymongo


def get_mongo_data(mongo_db, mongo_collection, contract):
    data = dict()
    query = {'contractName': contract}
    fields = {'_id': False}
    reports =  mongo_db[mongo_collection].find(
        query,
        fields)
    return reports


def set_mongo_data(mongo_db, mongo_collection, contract, mongo_data):
    try:
        result = mongo_db[mongo_collection].insert(
            mongo_data, continue_on_error=True)
    except pymongo.errors.DuplicateKeyError as e:
        print("Alguns informes del contracte " + contract + " ja existien.")
        print(str(e))
    except Exception as e:
        print("Error no controlat: " + str(e))
        return False
    return True


def main(contract, server):
    mongo_client_prod = pymongo.MongoClient(configdb.mongodb_prod)
    if server == 'terp01':
        mongo_client_test = pymongo.MongoClient(configdb.mongodb_test)
    elif server == 'perp01':
        mongo_client_test = pymongo.MongoClient(configdb.mongodb_pre)
    else:
        raise Exception("Servidor desconegut")

    mongo_db_prod = mongo_client_prod.somenergia
    mongo_db_test = mongo_client_test.somenergia

    reports = get_mongo_data(
        mongo_db=mongo_db_prod, mongo_collection='infoenergia_reports', contract=contract
    )

    print("Informes InfoEnergia obtinguts: " + str(reports.count()))

    if reports.count() > 0:
        result = set_mongo_data(
            mongo_db=mongo_db_test, mongo_collection='infoenergia_reports',
            contract=contract, mongo_data=reports
        )

    print("Els informes InfoEnergia disponibles s'han pujat a " + server)

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Copiar corbes a Testing')
    parser.add_argument('-c', '--contract',
        help="Escull per contract",
        )
    parser.add_argument('-s', '--server',
        help="Escull un servidor destí",
        )
    return parser.parse_args()

if __name__ == '__main__':
    args=parseargs()
    if not args.contract:
        fail("Introdueix un contract o el missatge d'error o una data")
    if not args.server:
        fail("Introdueix un servidor a on copiar les corbes")

    main(args.contract, args.server)
