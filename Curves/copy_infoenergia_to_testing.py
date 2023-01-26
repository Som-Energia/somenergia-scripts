#!/usr/bin/env python
# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()

from consolemsg import step, error, warn, fail, success
import pymongo
from curve_utils import (
    mongo_profile,
    mongo_profiles,
    join_cli_and_csv,
    contract_filter,
)

def get_mongo_data(mongo_db, mongo_collection, contracts):
    query = {
        'contractName': {'$in': contracts}
    }
    fields = {'_id': False}
    documents =  mongo_db[mongo_collection].find(
        query,
        fields)
    return documents


def set_mongo_data(mongo_db, mongo_collection, mongo_data):
    try:
        result = mongo_db[mongo_collection].insert(
            mongo_data, continue_on_error=True,
        )
    except pymongo.errors.DuplicateKeyError as e:
        warn("  Alguns informes ja existien.")
        warn("  {}",e)
        return True
    except Exception as e:
        error("Error no controlat: " + str(e))
        return False
    return True


def main(contracts, server):
    mongo_db_src = pymongo.MongoClient(mongo_profile('erp01')).somenergia
    mongo_db_dst = pymongo.MongoClient(mongo_profile(server)).somenergia

    step("Descarregant de {} informes pels contractes {}", server, contracts)
    reports = get_mongo_data(
        mongo_db=mongo_db_src,
        mongo_collection='infoenergia_reports',
        contracts=contracts,
    )

    success("Informes InfoEnergia obtinguts: " + str(reports.count()))

    if reports.count() > 0:
        step("Pujant informes a {}", server)
        result = set_mongo_data(
            mongo_db=mongo_db_dst,
            mongo_collection='infoenergia_reports',
            mongo_data=reports,
        )
    success("Els informes InfoEnergia disponibles s'han pujat a " + server)

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Copiar corbes a Testing')
    parser.add_argument(
        '--file',
        dest='csv_file',
        required=False,
        help="csv amb els números de contracte (a la primera columna i sense capçalera)"
    )
    parser.add_argument('-c', '--contract',
        help="Contracte a copiar",
        required=False,
    )
    parser.add_argument('-s', '--server',
        help="Servidor de destí",
        choices=[
            x
            for x in mongo_profiles().keys()
            if x != 'erp01'
        ]
    )
    return parser.parse_args()

if __name__ == '__main__':
    args=parseargs()
    if not args.contract and not args.csv_file:
        fail("Introdueix un contracte o fitxer amb els cups")
    if not args.server:
        fail("Introdueix un servidor a on copiar les corbes")

    contracts = join_cli_and_csv(cli=args.contract, csv_file=args.csv_file, filter=contract_filter)

    main(contracts, args.server)
