#!/usr/bin/env python
# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()

import configdb
from consolemsg import step, error, warn, fail, success, out
import pymongo
import csv

def get_mongo_data(mongo_db, mongo_collection, cups):
    query = {
        '$or': [
            {'name': {'$regex': '^{}'.format(acups[:20])}}
            for acups in cups
        ]
    }
    fields = {'_id': False}
    curves =  mongo_db[mongo_collection].find(
        query,
        fields)
    return curves


def set_mongo_data(mongo_db, mongo_collection, curve_type, mongo_data):
    try:
        result = mongo_db[mongo_collection].insert(
            mongo_data, continue_on_error=True,
        )
    except pymongo.errors.DuplicateKeyError as e:
        warn("Alguns registres de la corba " + curve_type + " ja existeixen.")
        warn(str(e))
        print(e.details)
        return False
    except Exception as e:
        error("Error no controlat: " + str(e))
        return False
    return result


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

    curves = dict(
        F5D = 'tg_cchfact',
        F1 = 'tg_f1',
        P5D = 'tg_cchval',
        P1 = 'tg_p1',
        TM_PROFILE = 'tm_profile',
        GENNETABETA = 'tg_cch_gennetabeta',
        AUTOCONS = 'tg_cch_autocons',
    )
    for name, collection in curves.items():
        step("Traspassant {}...".format(name))
        mongo_data = get_mongo_data(
            mongo_db=mongo_db_prod,
            mongo_collection=collection,
            cups=cups,
        )
        n_downloaded = mongo_data.count()

        step("  Corbes obtingudes {}: {}", name, n_downloaded)

        if mongo_data.count() > 0:
            result = set_mongo_data(
                mongo_db=mongo_db_test,
                mongo_collection=collection,
                curve_type=name,
                mongo_data=mongo_data,
            )
        success("  Done")

    print("Les corbes disponibles s'han pujat a " + server)


def format_cups(item):
    result = item.strip()[:20]
    if len(result) != 20:
        warn("Ignoring CUPS '{}'".format(result))
        return ''
    return result


def parse_csv(csv_file):
    if not csv_file: return []
    with open(csv_file) as f:
        reader = csv.reader(f)
        for row in reader:
            item = format_cups(row[0])
            if not item: continue
            yield item


def parse_comma_separated_list(inputstring):
    for item in inputstring.split(','):
        item = format_cups(item)
        if not item: continue
        yield item


def join_cli_and_csv(cli, csv_file):
    return list(set(
        parse_csv(csv_file)
    ).union(
        parse_comma_separated_list(cli)
    ))


def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Copiar corbes a Testing')
    parser.add_argument(
        '--file',
        dest='csv_file',
        required=False,
        help="csv amb el cups  (a la primera columna i sense capçalera)"
    )
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
    if not args.cups and not args.csv_file:
        fail("Introdueix un cups o fitxer amb els cups")
    if not args.server:
        fail("Introdueix un servidor a on copiar les corbes")

    cups = join_cli_and_csv(cli=args.cups, csv_file=args.csv_file)

    main(cups, args.server)
