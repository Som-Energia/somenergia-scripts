#!/usr/bin/env python
# -*- coding: utf-8 -*-
from future import standard_library
standard_library.install_aliases()

from consolemsg import step, error, warn, fail, success, out
import pymongo
import configdb
from erppeek import Client
from curve_utils import (
    mongo_profile,
    mongo_profiles,
    join_cli_and_csv,
    cups_filter,
)


def get_erp_client():
    """Connect to ERP"""
    return Client(**configdb.erppeek)


def get_member_ids_from_cups(cups_list, erp_client):
    """
    Given a list of CUPS, get the member_ids (somenergia.soci) associated
    through generationkwh.assignment table (not titular!)
    """
    member_ids = set()

    for cups in cups_list:
        # Find contract by CUPS
        contracts = erp_client.GiscedataPolissa.search([
            ('cups.name', '=', cups)
        ])
        if not contracts:
            warn("  No s'ha trobat contracte per CUPS: {}", cups)
            continue

        contract_id = contracts[0]

        # Find assignments for this contract (member -> contract relationship)
        assignments = erp_client.GenerationkwhAssignment.search([
            ('contract_id', '=', contract_id)
        ])

        if not assignments:
            warn("  No hi ha assignments per al contracte {}", cups)
            continue

        for assignment in erp_client.GenerationkwhAssignment.browse(assignments):
            member = assignment.member_id
            if member:
                member_id = member.name
                member_ids.add(member_id)
                step("  CUPS {} -> member {} (priority {})", cups, member_id, assignment.priority)

    return list(member_ids)


def get_mongo_data(mongo_db, mongo_collection, cups):
    query = {
        '$or': [
            {'name': {'$regex': '^{}'.format(acups[:20])}}
            for acups in cups
        ]
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
        warn("  Alguns registres ja existien.")
        warn("  {}",e)
        return True
    except Exception as e:
        error("Error no controlat: " + str(e))
        return False
    return True


def get_genkwh_rights(mongo_db_src, members=None):
    """Copy member rights from generationkwh, filtered by member_ids if provided"""
    collection = 'memberrightusage'
    if members:
        # Filter by member_ids
        query = {'name': {'$in': members}}
        documents = mongo_db_src[collection].find(query)
    else:
        # No filter - copy all (only used when no CUPS provided)
        documents = mongo_db_src[collection].find()
    return documents


def set_genkwh_rights(mongo_db_dst, mongo_data):
    """Insert member rights to destination"""
    collection = 'memberrightusage'
    try:
        result = mongo_db_dst[collection].insert(
            mongo_data, continue_on_error=True,
        )
    except pymongo.errors.DuplicateKeyError as e:
        warn("  Alguns registres ja existien.")
        warn("  {}",e)
        return True
    except Exception as e:
        error("Error no controlat: " + str(e))
        return False
    return True


def main(cups, server):
    mongo_db_src = pymongo.MongoClient(mongo_profile('erp01')).somenergia
    mongo_db_dst = pymongo.MongoClient(mongo_profile(server)).somenergia

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
            mongo_db=mongo_db_src,
            mongo_collection=collection,
            cups=cups,
        )
        n_downloaded = mongo_data.count()

        step("  Corbes obtingudes {}: {}", name, n_downloaded)

        if mongo_data.count() > 0:
            result = set_mongo_data(
                mongo_db=mongo_db_dst,
                mongo_collection=collection,
                mongo_data=mongo_data,
            )
        success("  Done")

    # Get members from CUPS via ERP
    if cups:
        step("Obtenint members dels CUPS...")
        erp_client = get_erp_client()
        members = get_member_ids_from_cups(cups, erp_client)

        if members:
            step("Traspassant drets de generationkwh dels members {}...".format(members))
            genkwh_data = get_genkwh_rights(mongo_db_src, members)
            n_genkwh = genkwh_data.count()

            step("  Drets obtinguts: {}", n_genkwh)

            if n_genkwh > 0:
                result = set_genkwh_rights(mongo_db_dst, genkwh_data)
            success("  Done")
            success("S'han copiat les corbes i drets de generationkwh dels CUPS a " + server)
        else:
            warn("No s'han trobat members per als CUPS especificats")
    else:
        success("S'han copiat les corbes a " + server)


def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Copiar corbes a Testing')
    parser.add_argument(
        '-f', '--file',
        dest='csv_file',
        required=False,
        help="csv amb el cups  (a la primera columna i sense capçalera)"
    )
    parser.add_argument('-c', '--cups',
        help="CUPS a copiar",
        required=False,
    )
    parser.add_argument('-s', '--server',
        help="Servidor destí",
        choices=[
            x
            for x in mongo_profiles().keys()
            if x != 'erp01'
        ]
    )
    return parser.parse_args()

if __name__ == '__main__':
    args=parseargs()
    if not args.cups and not args.csv_file:
        fail("Introdueix un cups o fitxer amb cups")
    if not args.server:
        fail("Introdueix un servidor a on copiar les corbes")

    cups = join_cli_and_csv(cli=args.cups, csv_file=args.csv_file, filter=cups_filter)

    main(cups, args.server)