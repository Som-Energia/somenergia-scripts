#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from sheetfetcher import SheetFetcher
import os
import io
from consolemsg import step, error, warn, fail
import csv
import psycopg2
import configdb
from dbutils import nsList, csvTable
import re




def get_dni_from_new_csv(config):

    fetcher = SheetFetcher(
        documentName = config.filename,
        credentialFilename = 'CredencialsBaixaSocis.json',
        )
#    load_data = fetcher.get_fullsheet(sheet)
    load_date = (",".join('\t'.join(c for c in row)
                 for row in fetcher.get_range(config.sheet, config.intervalCells4Date))).encode('utf-8').split(',')

    load_DNI =  (",".join('\t'.join(c for c in row)
                for row in fetcher.get_range(config.sheet, config.intervalCells4DNI))).encode('utf-8').split(',')
    load_DNI = [DNI.upper() for DNI in load_DNI]
    load_DNI = [re.sub('[^a-zA-Z0-9]+', '', dni) for dni in load_DNI]


    load_Check =  (",".join('\t'.join(c for c in row)
                for row in fetcher.get_range(config.sheet, config.intervalCells4Check))).encode('utf-8').split(',')
#    load_Name =  (",".join('\t'.join(c for c in row)
#                for row in fetcher.get_range(config.sheet, config.intervalCells4Name))).encode('utf-8').split(',')

    load_DNI = set(load_DNI)
    step("Saving data into {}", "migracio_baixa_socies.csv")
    with open("migracio_baixa_socies.csv", "w") as loadsocis:
         writer = csv.writer(loadsocis, delimiter = "\t")
         writer.writerows( zip(load_date, load_DNI, load_Check))
    return set(load_DNI)


def get_dni_from_erp(config):

    with io.open(config.queryfile) as f:
        query = f.read()
    
    step("Connecting to the ERP database...")
    db = psycopg2.connect(**configdb.psycopg)

    with db.cursor() as cursor :
        try:
            cursor.execute(query)
        except KeyError as e:
            fail("Missing variable '{key}'. Specify it in the YAML file or by using the --{key} option"
                .format(key=e.args[0]))
        erp_data =  nsList(cursor)

    print erp_data
    erp_data = [dict(dni) for dni in erp_data]
    erp_data = set((i['dni'] for i in erp_data))
   # print erp_data
    return erp_data




def main():
    

    step("Get all DNI from {} drive", config.filename)
    load_DNI = get_dni_from_new_csv(config)

    step("Get all DNI from ERP")
    load_erp_data = get_dni_from_erp(config)


    socis2migrate = set.intersection(load_DNI, load_erp_data)
    step("There are {} to migrate from {}", len(socis2migrate), config.filename)
   
    step("Get DNI from {}, that are in ERP but not in {}", config.oldFilename , config.filename)

     
 
if __name__ == '__main__':

    step('Loading Carregant configuració...')

    from yamlns import namespace as ns

    try:
        config = ns.load("config.yaml")
    except:
        error("Check config.yaml")
        raise

    main()
   




