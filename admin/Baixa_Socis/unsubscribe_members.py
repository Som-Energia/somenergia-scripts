# -*- encoding: utf-8 -*-
import argparse
import sys
import traceback
from hashlib import md5

import mailchimp_marketing as MailchimpMarketing
import requests
from consolemsg import step, error, success
from erppeek import Client
import time

import configdb


ERP_CLIENT = Client(**configdb.erppeek)
MAILCHIMP_CLIENT = MailchimpMarketing.Client(
    dict(api_key=configdb.MAILCHIMP_APIKEY, server=configdb.MAILCHIMP_SERVER_PREFIX)
)


def get_member_category_id():
    module = 'som_partner_account'
    semantic_id = 'res_partner_category_soci'
    IrModelData = ERP_CLIENT.model('ir.model.data')
    
    member_category_relation = IrModelData.get_object_reference(
        module, semantic_id
    )
    if member_category_relation:
        return member_category_relation[-1]


def get_not_members_email_list():
    Soci = ERP_CLIENT.model('somenergia.soci')
    ResPartnerAddress = ERP_CLIENT.model('res.partner.address')
    category_id = get_member_category_id()

    not_members = Soci.search([
        ('category_id', 'not in', [category_id]),
        ('ref', 'like', 'S%')
    ])
    not_members_partner_ids = [
        soci['partner_id'][0] for soci in Soci.read(not_members, ['partner_id'])
    ]
    address_list = ResPartnerAddress.search(
        [('partner_id', 'in', not_members_partner_ids)]
    )

    emails_list = [
        address.get('email', 'not found')
        for address in ResPartnerAddress.read(address_list, ['email'])
    ]

    return emails_list


def get_mailchimp_list_id(list_name):
    all_lists = MAILCHIMP_CLIENT.lists.get_all_lists(
        fields=['lists.id,lists.name'],
        count=100
    )['lists']
    for l in all_lists:
        if l['name'] == list_name:
            return l['id']
    raise Exception("List: <{}> not found".format(list_name))


def get_subscriber_hash(email):
    subscriber_hash = md5(email.lower()).hexdigest()
    return subscriber_hash


def archive_members_from_list(list_name, email_list):
    list_id = get_mailchimp_list_id(list_name)
    operations = []
    for email in email_list:
	operation = {
            "method": "DELETE",
            "path": "/lists/{list_id}/members/{subscriber_hash}".format(
                list_id=list_id,
                subscriber_hash=get_subscriber_hash(email)
            ),
            "operation_id": email,
        }
        operations.append(operation)
    payload = {
        "operations": operations
    }
    try:
        response = MAILCHIMP_CLIENT.batches.start(payload)
    except ApiClientError as error:
        msg = "An error occurred an archiving batch request, reason: {}"
        error(msg.format(error.text))
    else:
        batch_id = response['id']
        while response['status'] != 'finished':
            time.sleep(2)
            response = MAILCHIMP_CLIENT.batches.status(batch_id)

        step("Archived operation finished!!")
        step("Total operations: {}, finished operations: {}, errored operations: {}".format(
            response['total_operations'],
            response['finished_operations'],
            response['errored_operations']
        ))
        result_summary = requests.get(response['response_body_url'])
        result_summary.raise_for_status()
        return result_summary.content


def archieve_members_in_list(list_name):
    email_list = get_not_members_email_list()
    result = archive_members_from_list(list_name, email_list)

    return result


def main(list_name, output):

    result =  archieve_members_in_list(list_name.strip())

    with open(output, 'w') as f:
        f.write(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Archivieren Sie E-Mails in großen Mengen'
    )

    parser.add_argument(
        '--list',
        dest='list_name',
        required=True,
        help="nom de la llista de mailchimp"
    )

    parser.add_argument(
        '--output',
        dest='output',
        required=True,
        help="Fitxer de sortida amb els resultats"
    )

    args = parser.parse_args()
    try:
        main(args.list_name, args.output)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proceso no ha finalizado correctamente: {}", str(e))
    else:
        success("Script finalizado")
