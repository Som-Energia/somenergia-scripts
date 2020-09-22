#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from yamlns import namespace as ns
from consolemsg import step, success, warn
import csv
import time
import argparse

O = None
doit = False
EMAIL_TEMPLATE_ID = 308
EMAIL_FROM_ACCOUNT = 16
CONTRACTS_PER_BATCH = 100
TIME_BETWEEN_BATCHS = 1


def connect_erp():
    global O
    if O:
        return O
    step("Connectant a l'erp")
    O = Client(**configdb.erppeek)
    step("connectat...")
    return O


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Envia correus d'avis de mort al pagador"
    )

    parser.add_argument(
        '--file',
        dest='csv_file',
        required=True,
        help="csv amb les polisses a avisar"
    )

    parser.add_argument(
        '--doit',
        type=bool,
        default=False,
        const=True,
        nargs='?',
        help='realitza les accions'
    )

    args = parser.parse_args()
    if args.doit:
        success("Es faran enviament de correus (--doit)")
    else:
        success("No es faran enviament de correus (sense opció --doit)")
    global doit
    doit = args.doit

    return args


def read_data_from_csv(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f, delimiter=';')
        header = reader.next()

        # check if file is utf8 + BOM
        if '\xef\xbb\xbf' in header[0]:
            raise IOError

        if len(header) == 1:
            reader = csv.reader(f, delimiter=',')
            header = header[0].split(',')

        csv_content = [ns(dict(zip(header, row))) for row in reader if row[0]]

    return csv_content


def get_polissa_ids_from_csv(filename):
    pol_ids = []
    for contract_name in read_data_from_csv(filename):
        pol_obj = O.GiscedataPolissa

        name = contract_name.contracte.zfill(7)
        pol_id = pol_obj.search([('name', '=', name)])
        if len(pol_id) > 1:
            warn("Multiples resultats per polissa {} : {}",
                 name, pol_id)
        elif len(pol_id) == 0:
            warn("Sense resultats per polissa {}", name)
        else:
            if pol_id[0] not in pol_ids:
                pol_ids.extend(pol_id)
    return pol_ids


def send_erp_email(obj_id, obj_model, template_id, from_id):
    ctx = {
        'active_ids': [obj_id],
        'active_id': obj_id,
        'template_id': template_id,
        'src_model': obj_model,
        'src_rec_ids': [obj_id],
        'from': from_id,
        }
    params = {'state': 'single', 'priority': 0, 'from': ctx['from']}
    wiz = O.PoweremailSendWizard.create(params, ctx)
    O.PoweremailSendWizard.send_mail([wiz.id], ctx)


def send_contract_erp_email(pol_id):
    step("Enviant correus a la polissa id {}", pol_id)
    if doit:
        send_erp_email(pol_id, 'giscedata.polissa',
                       EMAIL_TEMPLATE_ID,
                       EMAIL_FROM_ACCOUNT)
    else:
        warn("email sending disabled, set --doit.")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in xrange(0, len(lst), n):
        yield lst[i:i + n]


def send_killing_payer_email_warning(pol_ids):
    first = True
    for batch in chunks(pol_ids, CONTRACTS_PER_BATCH):
        if not first:
            step("Esperant {} segons per no saturar", TIME_BETWEEN_BATCHS)
            time.sleep(TIME_BETWEEN_BATCHS)

        success("Enviant email a bloc de {} polisses.", len(batch))
        for pol_id in batch:
            send_contract_erp_email(pol_id)


if __name__ == '__main__':
    args = parse_arguments()
    O = connect_erp()

    pol_ids = get_polissa_ids_from_csv(args.csv_file)
    success("Extrets {} id's de polisses del csv", len(pol_ids))
    send_killing_payer_email_warning(pol_ids)
    success("Correus Enviats")

# vim: et ts=4 sw=4
