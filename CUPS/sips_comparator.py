#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import csv
import tqdm
import click
from erppeek import Client
from datetime import datetime, date

import configdb

ATR_CASES = ['C2']


def create_file(c, from_date, file_output):
    p_ids = c.GiscedataPolissa.search(
        [('data_firma_contracte', '>=', from_date)]
    )
    print "{} contracts found from date {}".format(len(p_ids), from_date)
    print "Dumping data to {}".format(file_output)
    if not p_ids:
        print "No contracts found"
        return

    with open(file_output, 'w') as csvfile:
        fields = ['contrato', 'cups', 'data_alta', 'adr_cups', 'adr_sips', 'poblacio_sips', 'titular', 'titular_email']
        csvwriter = csv.writer(csvfile, delimiter=';')
        csvwriter.writerow(fields)
        p_fields = ['name', 'data_alta', 'cups', 'titular']
        for p_data in tqdm.tqdm(c.GiscedataPolissa.read(p_ids, p_fields)):
            contract_name = p_data['name']
            contract_id = p_data['id']
            cups_id = p_data['cups'][0]
            titular_id = p_data['titular'][0]
            titular_name = p_data['titular'][1]
            cups_name = p_data['cups'][1]
            # Only with ATR case
            atr_ids = c.GiscedataSwitching.search([
                ('cups_polissa_id', '=', contract_id),
                ('proces_id.name', 'in', ATR_CASES)
            ])
            if not atr_ids:
                continue
            c_data = c.GiscedataCupsPs.read(cups_id, ['name', 'direccio'])
            t_data = c.ResPartner.read(titular_id, ['name', 'lang', 'vat'])
            pa_ids = c.ResPartnerAddress.search([('partner_id', '=', titular_id)])
            email = ''
            for pa_data in c.ResPartnerAddress.read(pa_ids, ['email']):
                if pa_data['email']:
                    email = pa_data['email']
                    break
            sips_ids = c.GiscedataSipsPs.search(
                [('name', 'in', [cups_name, cups_name[:20]])]
            )
            data = [
                contract_name, cups_name, p_data['data_alta'],
                c_data['direccio'].encode('utf-8')
            ]
            if sips_ids:
                sips_id = int(sips_ids[0])
                sips_data = c.GiscedataSipsPs.read(
                    sips_id, ['poblacio', 'direccio']
                )
                sips_dir = sips_data.get('direccio', u'').encode('utf-8')
                sips_poblacio = sips_data.get('poblacio', u'').encode('utf-8')
                extra_sips = [sips_dir, sips_poblacio]
            else:
                extra_sips = ["No SIPS Found", ""]
            data.extend(extra_sips)
            data.extend([titular_name.encode('utf-8'), email, t_data['lang']])
            csvwriter.writerow(data)


@click.command()
@click.option('-f', '--file-output', default='/tmp/sips_comparator.csv',
              help='Destination file path')
@click.option('-d', '--from-date',
              default=datetime.today().date().strftime('%Y-%m-%d'),
              help='Contract start date to comparei [YYYY-MM-DD]')
def main(**kwargs):
    c = Client(**configdb.erppeek)
    print "connected to: {}".format(c._server)
    create_file(c, kwargs['from_date'], kwargs['file_output'])


if __name__ == '__main__':
    main()
