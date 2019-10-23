#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, io, os
import csv
import collections
import traceback
from operator import itemgetter
from datetime import datetime

import configdb
from ooop import OOOP
from sheetfetcher import SheetFetcher
from consolemsg import step, error, warn, fail, success
from emili import sendMail
from scripts.utils import get_data_from_erp


def process_records(erp_data, pfilename):
    '''
    This function retrieves the incoherent data
    from ERP
    '''

    erp_data = [dict(data) for data in erp_data]
    filename = pfilename+datetime.now().strftime("%Y%m%d")+'.csv'
    if erp_data:
        error("\tThere are {} incoherent records in {}", len(erp_data), datetime.now().strftime("%Y-%m-%d"))
        error("\tSaving incoherent  data in {}" , filename)
        header = {key for d in erp_data for key in d.keys()}
        with open(filename, "w") as loadsocis:
            writer = csv.DictWriter(loadsocis, header) 
            writer.writeheader()
            writer.writerows(erp_data)    
    else:
        success("\tPerfect! There is nothing to do! No incoherent records found in {}", datetime.now().strftime("%Y-%m-%d"))
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
        if janitor.get('query', True):
            erp_data = get_data_from_erp(janitor.sql)
            allData, filename = process_records(
                erp_data,
                janitor.output
                )
            if allData:
                sendmail2all(janitor, filename)
        else:
            os.system(janitor.python)
    
if __name__ == '__main__':

    step('Loading config file...')

    from yamlns import namespace as ns

    try:
        config = ns.load("config.yaml")
    except:
        error("Check config.yaml")
        raise

    janitor_execution(config)
    success("Done!")
