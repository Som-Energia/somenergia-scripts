# -*- encoding: utf-8 -*-
import argparse
import sys
import traceback
from consolemsg import step, error, success
from erppeek import Client
import dbconfig

from archive_utils import read_data_from_csv, archive_clients_from_list

ERP_CLIENT = Client(**dbconfig.erppeek)

doit = False

def is_titular_partner_mail(email):

    email_ids = ERP_CLIENT.ResPartnerAddress.search([('email', '=', email)])
    if not email_ids:
        return False
    partners_ids = [
        item['partner_id'][0]
        for item in ERP_CLIENT.ResPartnerAddress.read(email_ids, ['partner_id'])
        if item and 'partner_id' in item and item['partner_id']
    ]

    polisses_ids = ERP_CLIENT.GiscedataPolissa.search([('titular','in',partners_ids)])
    if not polisses_ids:
        return False

    return True

def get_not_active(emails):
    to_archive = []
    total = len(emails)
    for counter, email in enumerate(emails):
        if not is_titular_partner_mail(email):
            to_archive.append(email)
            step("{}/{} - {} --> no titular", counter+1, total, email)
        else:
            step("{}/{} - {} --> titular", counter+1, total, email)
    return to_archive

def main(list_name, mailchimp_export_file, output):

    csv_data = read_data_from_csv(mailchimp_export_file)
    step("{} lines read from input csv", len(csv_data))

    mails = [item['Email Address'] for item in csv_data]
    step("{} emails extracted from input csv", len(mails))

    to_archive = get_not_active(mails)
    step("{} emails to archive found", len(to_archive))

    result = ''
    if doit:
        step("archiving...")
        result = archive_clients_from_list(list_name.strip(), to_archive)

    step("storing result {}", len(result))
    with open(output, 'w') as f:
        f.write("Emails to be archived\n---------------------\n")
        f.write("\n".join(to_archive))
        f.write("\nMailchimp Api responses\n-----------------------\n")
        f.write(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description=''
    )

    parser.add_argument(
        '--list',
        dest='list_name',
        required=True,
        help="nom de la llista de mailchimp"
    )

    parser.add_argument(
        '--mailchimp_export_file',
        dest='mailchimp_export_file',
        required=True,
        help="Fitxer amb export del mailchimp"
    )

    parser.add_argument(
        '--output',
        dest='output',
        required=True,
        help="Fitxer de sortida amb els resultats"
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

    global doit
    doit = args.doit
    if doit:
        success("Es faran canvis a les polisses (--doit)")
    else:
        success("No es faran canvis a les polisses (sense opció --doit)")

    try:
        main(args.list_name, args.mailchimp_export_file, args.output)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proceso no ha finalizado correctamente: {}", str(e))
    else:
        success("Script finalizado")
