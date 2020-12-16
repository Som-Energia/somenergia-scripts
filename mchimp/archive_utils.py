# -*- encoding: utf-8 -*-
import csv
from hashlib import md5
from yamlns import namespace as ns
import requests
import time
import dbconfig
import mailchimp_marketing as MailchimpMarketing


MAILCHIMP_CLIENT = MailchimpMarketing.Client(
    dict(api_key=dbconfig.MAILCHIMP_APIKEY, server=dbconfig.MAILCHIMP_SERVER_PREFIX)
)

def read_data_from_csv(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        header = reader.next()

        # check if file is utf8 + BOM
        if '\xef\xbb\xbf' in header[0]:
            raise IOError

        if len(header) == 1:
            reader = csv.reader(f, delimiter=',')
            header = header[0].split(',')

        csv_content = [ns(dict(zip(header, row))) for row in reader if row[0]]

    return csv_content

def get_subscriber_hash(email):
    subscriber_hash = md5(email.lower()).hexdigest()
    return subscriber_hash

def get_mailchimp_list_id(list_name):
    all_lists = MAILCHIMP_CLIENT.lists.get_all_lists(
        fields=['lists.id,lists.name'],
        count=100
    )['lists']
    for l in all_lists:
        if l['name'] == list_name:
            return l['id']
    raise Exception("List: <{}> not found".format(list_name))

def archive_clients_from_list(list_name, email_list):
    if not doit:
        return ""

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
