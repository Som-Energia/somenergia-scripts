#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, io, os
import csv
import collections
import traceback
from dbutils import nsList, csvTable
from operator import itemgetter
from datetime import datetime

import psycopg2
import configdb
from ooop import OOOP
from sheetfetcher import SheetFetcher
from consolemsg import step, error, warn, fail
from emili import sendMail

def get_data_from_erp(queryfile, pfilename):
    '''
    This function retrieves the incoherent data
    from ERP
    '''
    with io.open(queryfile) as f:
        query = f.read()
    db = psycopg2.connect(**configdb.psycopg)
    with db.cursor() as cursor :
        try:
            cursor.execute(query)
        except KeyError as e:
            fail("Missing variable '{key}'. Specify it in the YAML file or by using the --{key} option"
                .format(key=e.args[0]))
        erp_data =  nsList(cursor)
    erp_data = [dict(data) for data in erp_data]
    filename = pfilename+datetime.now().strftime("%Y%m%d")+'.csv'
    if erp_data:
        step("There are {} incoherent records in {}", len(erp_data), datetime.now().strftime("%Y-%m-%d"))
        step("Saving incoherent  data in {}" , filename)
        header = {key for d in erp_data for key in d.keys()}
        with open(filename, "w") as loadsocis:
            writer = csv.DictWriter(loadsocis, header) 
            writer.writeheader()
            writer.writerows(erp_data)    
    else:
        step("Perfect! There is nothing to do! No incoherent records found in {}", datetime.now().strftime("%Y-%m-%d"))
    return erp_data, filename   
 
def sendmail2all(janitor, attachment):
    '''
    Sends the incoherent data by email 
    '''
    sendMail(
        sender = janitor.sender,
        to =  janitor.recipients,
        bcc = janitor.bcc,
        subject = janitor.subject,
        md = janitor.content,
        attachments = [attachment],
        config = 'configdb.py',
    )

def janitor_execution(config):
    '''
    For each janitor defined in the yaml file
    checks for incoherent data and send it by email
    '''
    for name, janitor in config.items():
        if not janitor.get('active',False):
            warn("Skipping janitor: {name}", name=name)
            continue
        step("Running janitor: {description}",**janitor)
        allData, filename = get_data_from_erp(
            janitor.sql,
            janitor.output
            )    
        if allData:
            sendmail2all(janitor, filename)

    
if __name__ == '__main__':

    step('Loading config file...')

    from yamlns import namespace as ns

    try:
        config = ns.load("config.yaml")
    except:
        error("Check config.yaml")
        raise

    janitor_execution(config)
    step("Done!")
