#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, io, os
import datetime
import collections
import csv
import re
import psycopg2
import configdb

from sheetfetcher import SheetFetcher
from consolemsg import step, error, warn, fail
from ooop import OOOP
from dbutils import nsList, csvTable
from stdnum.es import nif as evalnif
from operator import itemgetter
from dateutil.parser import parse
from unidecode import unidecode
from yamlns import namespace as ns

def validate_dates(load_data, socis2migrate, filename):
    '''
    Checks for incorrect date format:
    in case of incorrect format, it saves soci's NIF and the
    incorrect date in a csv file for correction.
    Returns the correct date found and NIF.
    '''
    get_nif = itemgetter(0)
    get_fecha = itemgetter(1)

    data_baixa = []
    wrong_data_baixa = []
    soci = []
    wrong_data_soci = []
    initial_nif_list = [get_nif(elem) for elem in load_data]
    for elem in load_data:
        if get_nif(elem) in socis2migrate:
            try: 
                parse(get_fecha(elem))
                soci.append(get_nif(elem))
                data_baixa.append(get_fecha(elem))
            except ValueError:
                check4double_dni = [item for item, count in collections.Counter(initial_nif_list).items() if get_nif(elem) in item if count > 1]
                if len(check4double_dni) > 0: 
                    continue 
                else:
                    wrong_data_baixa.append(get_fecha(elem))
                    wrong_data_soci.append(get_nif(elem))
    with open(filename, "w") as loadfechas:
        writer = csv.writer(loadfechas, delimiter = "\t")
        writer.writerows( zip(wrong_data_soci, wrong_data_baixa))
    return soci,  data_baixa



def get_real_nif(nif, name, filename):
    '''
    Checks for incorrect NIF format:
    in case of incorrect format, it saves soci's name and NIF
    in a csv file for correction.
    Returns correct and incorrect NIFs in separate lists
    '''
    get_nif = itemgetter(0)
    get_name = itemgetter(1)
    get_ok = itemgetter(2)

    real_nif = []
    wrong_nif = []
    wrong_name = []
    initial_nif_list = [get_nif(elem) for elem in name]
 
    for elem in name:
         if get_ok(elem) == 'OK':
            if get_nif(elem) in nif:
                try:
                    real_nif.append(evalnif.validate(get_nif(elem)))
                except: 
                    wrong_nif.append(get_nif(elem))
                    wrong_name.append(get_name(elem))
                    pass 
    with open(filename, "w") as loadDNI:
        writer = csv.writer(loadDNI, delimiter = "\t")
        writer.writerows(zip(wrong_nif, wrong_name) )
    return set(real_nif), wrong_nif


def get_date(baixa_erp):

    get_dateI = itemgetter(0)
    get_dateF = itemgetter(1)
    get_ref = itemgetter(2)
    get_ok = itemgetter(3)

    soci_ref = []
    data_baixa = []
    for elem in baixa_erp:
         if get_ok(elem) == 'SI':
            try:
                parse(get_dateF(elem))
                data_baixa.append(get_dateF(elem))
                soci_ref.append(get_ref(elem))
            except ValueError:
                data_baixa.append(get_dateI(elem))
                soci_ref.append(get_ref(elem))
     
    return soci_ref, zip(soci_ref, data_baixa)  


def get_nif_from_csv(config):
    '''
    Find the NIF for each 'soci' that are in a csv file.
    '''

    fetcher = SheetFetcher(
        documentName = config.filename,
        credentialFilename = 'CredencialsBaixaSocis.json',
        )

    load_dateI = [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4DateI)]
    load_dateF = [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4DateF)]
    load_nif = [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4DNI)]
    load_nif = [re.sub('[^a-zA-Z0-9]+', '', nif).upper() for nif in load_nif]
    load_Check = [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4Check)]
    load_Check = [re.sub('[^a-zA-Z]+', '', i).upper() for i in load_Check]
    load_name = [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4Name)]

    name = zip(load_nif, load_name, load_Check)
    load_data = zip(load_nif, load_dateF)
    load_real_nif, wrong_nif = get_real_nif(load_nif, name, 'DNI_a_verificar_migracion.csv')

    warn("There are {} DNI that are duplicated and {} that are misinformed, from the initial {} in {}",
                   len(load_nif) - len(set(load_nif)), len(wrong_nif), len(load_nif), config.filename)
    return load_real_nif, load_data


def get_data_from_erp(queryfile, filename):
    '''
    Find the 'socis' from ERP that need a cancelation date.
    '''
    with io.open(queryfile) as f:
        query = f.read()

    step("Connecting to the ERP database...")
    db = psycopg2.connect(**configdb.psycopg)

    with db.cursor() as cursor:
        try:
            cursor.execute(query)
        except KeyError as e:
            fail("Missing variable '{key}'. Specify it in the YAML file or by using the --{key} option"
                .format(key=e.args[0]))
        erp_data =  nsList(cursor)

    erp_data = [dict(data) for data in erp_data]
    erp_count_duplicated = collections.Counter(i['nif'] for i in erp_data)
    erp_duplicated = collections.Counter({elem: count for elem, count in erp_count_duplicated.iteritems() if count > 1 })
    warn("There are {} duplicated records:{}", len(erp_duplicated), erp_duplicated)

    erp_nif = set(i['nif'] for i in erp_data)
    erp_ref = set(i['ref_cliente'] for i in erp_data)
    erp_vat = [i['vat'] for i in erp_data]
    erp_categoria = [i['categoria'] for i in erp_data]
    erp_name = [i['name'] for i in erp_data]

    step("Saving ERP data in {}, there are {} cases that meet the migration criteria" , filename, len(erp_nif))
    with open(filename, "w") as loadsocis:
        writer = csv.writer(loadsocis, delimiter = "\t")
        writer.writerows( zip(erp_vat, erp_ref, erp_categoria, erp_name)) 
    return erp_nif, erp_data


def get_ref_from_csv(config):
    '''
    Find socis' code number from csv file.
    '''
    fetcher = SheetFetcher(
        documentName = config.filename,
        credentialFilename = 'CredencialsBaixaSocis.json',
        )

    load_dateI =  [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4DateI)]
    load_dateF = [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4DateF)]
    load_refsoci = [row[0].encode('utf-8') for row in fetcher.get_range(config.sheet, config.intervalCells4DNI)]
    load_Check = [unidecode(row[0]).encode('ascii') for row in fetcher.get_range(config.sheet, config.intervalCells4Check)]
    load_Check = [re.sub('[^a-zA-Z]+', '', i).upper() for i in load_Check]
    load_refsoci = [re.sub('[^0-9]+', '', ref) for ref in load_refsoci]
    load_refsoci = [('{num:06d}'.format(num=int(i))) for i in load_refsoci if i]
    load_refsoci = ['{}{}'.format( 'S', soci) for soci in load_refsoci]

    baixa_erp = zip(load_dateI, load_dateF, load_refsoci, load_Check)

    check_refsoci = len(load_refsoci)
    load_refsoci = set(load_refsoci)

    refsoci, refdata = get_date(baixa_erp)
    warn("There are {} soci number that are duplicated, from the initial {} in {}", check_refsoci - len(load_refsoci), check_refsoci, config.filename)
    return refsoci, refdata


def update_ERP(configdb, socis, data_baixa, codi, filename):
    '''
    Update 'data_baixa_soci' field in ERP.
    '''
    O = OOOP(**configdb.ooop)
    Partner = O.ResPartner
    Soci = O.SomenergiaSoci

    step("Update all Non-Active socis in {}", filename)
    baixas_id_no_activas = [Soci.search([((codi), "like", soci), ("active", "=", False)]) for soci in socis if Soci.search([((codi), "like", soci), ("active", "=", False)]) ]
    all_inactive_categories = [Soci.read(item)['category_id'] for idlist in baixas_id_no_activas for item in idlist]
    for soci in xrange(len(all_inactive_categories)):
        keep_inactive_categories = [category for category in all_inactive_categories[soci] if category <> 8]
        Soci.write(baixas_id_no_activas[soci] , {'active': False, 'baixa': True , 'category_id': [(6, 0, keep_inactive_categories)], 'data_baixa_soci': data_baixa[soci] } )


def migrate_socis(config, query, output):
    '''
    Migrates cancelation date from both excels into ERP
    In case there are socis missing from both excels, save their data in a file
    for hand correction.
    '''
    step("Get DNI from {} drive", config.newDrive.filename)
    load_DNI, load_data = get_nif_from_csv(config.newDrive)

    load_erp_nif, load_erp_data = get_data_from_erp(query, output)
    socis2migrate = list(set.intersection(load_erp_nif, load_DNI))

    step("There are {} to migrate from {}", len(socis2migrate), config.newDrive.filename)
    soci, data_baixa  = validate_dates(load_data, socis2migrate, "corregir_fechas_Baixa_socis.csv")
    update_ERP(configdb, soci, data_baixa, "vat", config.newDrive.filename)

    othersocis = load_erp_nif.difference(load_DNI)
    othersocis_ref =  [i['ref_cliente'] for i in load_erp_data if 'nif' in i  if i['nif'] in othersocis]
    step("Get DNI from {}, that are in ERP but not in {}", config.oldDrive.filename , config.newDrive.filename)
    load_ref, data_ref = get_ref_from_csv(config.oldDrive)

    socis2migrate_ref = set.intersection(set(load_ref), set(othersocis_ref))
    soci_ref, data_baixa_ref  = validate_dates(data_ref, socis2migrate_ref, "corregir_fechas_Baixes_de_soci.csv")

    step("There are {} to migrate from {}", len(socis2migrate_ref), config.oldDrive.filename)
    update_ERP(configdb, soci_ref, data_baixa_ref, "ref", config.oldDrive.filename)
    missing_socis = set(othersocis_ref).difference(socis2migrate_ref)
    warn("There are {} 'socis' missing from both excels and need to be updated.", len(missing_socis))

    step("Saving missing 'socis' into {}", "hand_migration.csv")
    with open("hand_migration.csv", "w") as loadsocis:
         writer = csv.writer(loadsocis, delimiter = "\t")
         writer.writerows(missing_socis)


def find_and_fix_soci_record(query, output):
    '''
    Find 'socis' that have no record in somenergia_soci and create one.
    '''
    O = OOOP(**configdb.ooop)
    with io.open(query) as f:
        query = f.read()

    step("Connecting to the ERP database...")
    db = psycopg2.connect(**configdb.psycopg)

    with db.cursor() as cursor:
        try:
            cursor.execute(query)
        except KeyError as e:
            fail("Missing variable '{key}'. Specify it in the YAML file or by using the --{key} option"
                .format(key=e.args[0]))
        erp_data =  nsList(cursor)

    erp_data = [dict(data) for data in erp_data]
    erp_ids = set(i['ids'] for i in erp_data)
    erp_soci = set(i['ref'] for i in erp_data)
    for partner_id in erp_ids:
        get_or_create_somenergia_soci(O, partner_id)

    with open(output, "w") as loadsocis:
         writer = csv.writer(loadsocis, delimiter = "\t")
         writer.writerows(zip(erp_ids, erp_soci))


def get_or_create_somenergia_soci(t, partner_id):
    '''
        Function taken from: webforms/webforms/model.py --> new_soci()
        Returns the Somenergia soci, or creates it
        if it does not exist.
    '''
    soci_ids = t.SomenergiaSoci.search([
        ('partner_id','=',partner_id),
        ])
    if soci_ids: return soci_ids[0]

    return t.SomenergiaSoci.create_one_soci(partner_id)


if __name__ == '__main__':

    step('Loading config file...')

    try:
        config = ns.load("config.yaml")
    except:
        error("Check config.yaml")
        raise

    step("Find and create 'socis' with no record in somenergia_soci")
    find_and_fix_soci_record(config.query_no_record_socis.sql, config.query_no_record_socis.output)

    step("Get socis considering: {}", config.queryfile1.sql)
    migrate_socis(config, config.queryfile1.sql, config.queryfile1.output)

    step("Migration completed!")
