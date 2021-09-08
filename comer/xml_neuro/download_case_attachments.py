# -*- encoding: utf-8 -*-
from __future__ import print_function, unicode_literals

import argparse
import base64
import csv
import sys
import traceback
from collections import namedtuple
from os import name, path
from zipfile import ZipFile

from consolemsg import error, step, success
from erppeek import Client

import configdb

c = Client(**configdb.erppeek)

Switching = c.model('giscedata.switching')

Attachment = namedtuple('Attachment', 'name, data')

'''
Example of csv
cups
ES0223000033002674TF;
ES0021011010463809XW;
ES0021000014495564TA;
'''

def csv_to_cups(cups_csv):
    with open(cups_csv) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=str(u';').encode('utf-8'))
        cupses = [row['cups'] for row in reader]

    return cupses


def augmented_name(file_name, cups, creation_date):
    creation_date = creation_date.replace(' ', 'T')
    return '{}_{}_{}'.format(cups, creation_date, file_name)


def get_cups_xmls(cups):
    attachments = []
    
    step('get xmls from {}'.format(cups))
    switches = Switching.search([('cups_id.name', 'ilike', cups)])
    for sw_id in switches:
        sw = Switching.browse(sw_id)
        if sw._attachments_field.name != []:
            for name, data, creation_date in zip(
                sw._attachments_field.name, sw._attachments_field.datas, sw._attachments_field.create_date
            ):
                attachments.append(
                    Attachment(augmented_name(name, cups, creation_date), base64.decodestring(data))
                )
    return attachments


def archive(zipfile, attachments):
    for attachment in attachments:
        zipfile.writestr(attachment.name, attachment.data)


def download_xmls(cupses, output_file):
    with ZipFile(output_file, 'w') as zip_:
        for cups in cupses:
            attachments = get_cups_xmls(cups)
            archive(zip_, attachments)


def main(cups_csv, output_file):
    cupses = csv_to_cups(cups_csv)
    download_xmls(cupses, output_file)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Unterladen Sie Anhang von ATR Fälle'
    )

    parser.add_argument(
        '--file',
        dest='cups_csv',
        required=True,
        help="csv amb els cups per descarregar els adjunts del seus casos ATR"
    )
    
    parser.add_argument(
        '--output',
        dest='output_file',
        required=True,
        help="Fitxer de sortida amb els resultats"
    )

    args = parser.parse_args()
    try:
        main(args.cups_csv, args.output_file)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proceso no ha finalizado correctamente: {}", str(e))
    else:
        success("Script finalizado")
