#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import csv
import tqdm
import click
from erppeek import Client
from datetime import datetime, date

import configdb

ATR_CASES = ['C2']
ATR_STEPS = ['01']

def create_file(c, from_date, file_output):
    atr_ids = c.GiscedataSwitching.search([('create_date','>=', from_date),('proces_id.name', 'in', ATR_CASES),('step_id.name','in',ATR_STEPS)])

    print "{} contracts found from date {}".format(len(atr_ids), from_date)
    print "Dumping data to {}".format(file_output)

    if not atr_ids:
        print "No ATR cases found"
        return

    polisses = c.GiscedataSwitching.read(atr_ids, ['cups_polissa_id','user_id'])
    polisses_ids = set([polissa['cups_polissa_id'][0] for polissa in polisses if polissa['cups_polissa_id']])
    polisses_with_resp = dict( [polissa['cups_polissa_id'][0],polissa['user_id'][1]] for polissa in polisses if polissa['cups_polissa_id'] and polissa['user_id'] )

    with open(file_output, 'w') as csvfile:
        fields = ['contrato', 'cups', 'data_alta', 'adr_cups', 'adr_sips', 'poblacio_sips', 'titular', 'titular_email', 'responsable', 'idioma']
        csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC ,quotechar ='\"', delimiter=';')
        csvwriter.writerow(fields)
        p_fields = ['name', 'data_alta', 'cups', 'titular']

        for p_data in tqdm.tqdm(c.GiscedataPolissa.read(list(polisses_ids), p_fields)):
            contract_name = p_data['name']
            contract_id = p_data['id']
            cups_id = p_data['cups'][0]
            titular_id = p_data['titular'][0]
            titular_name = p_data['titular'][1]
            cups_name = p_data['cups'][1]

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
            resp = polisses_with_resp[p_data['id']].encode('utf-8') 
            data.extend([titular_name.encode('utf-8'), email, resp, t_data['lang']])
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
