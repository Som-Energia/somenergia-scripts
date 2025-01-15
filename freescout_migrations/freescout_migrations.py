# -*- coding: utf-8 -*-
import click
import csv
import requests
from configdb import URL, SECRET_KEY, HS_TOKEN, EMAIL_FILENAME
from create_conversation import create_conversation
from tqdm import tqdm
from migration_checks import customer_email_in_erp, newer_than_4y


HS_HEADERS = {
    'Authorization': f'Bearer {HS_TOKEN}',
    'Content-Type': 'application/json'
}

FS_HEADERS = {
    "X-FreeScout-API-Key": SECRET_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

POST_CONVERSATION_URL = "{}{}".format(URL, 'conversations')
ADD_TAGS_URL = "{}{}".format(URL, 'conversations/{}/tags')


def get_tqdm(url):
    response = requests.get(url, headers=HS_HEADERS)
    page_info = response.json().get('page', {})
    return tqdm(total=page_info.get('totalElements', 0)), page_info.get('size', 1)


def read_csv_emails(filename):
    with open(filename, mode='r') as file:
        csvFile = csv.reader(file)
        emails={line[0] for line in csvFile}
    return emails


@click.command()
@click.option('-s', '--start-date', required=True,
              help='Format: 2022-02-01T23:59:59Z')
@click.option('-e', '--end-date', required=True,
              help='Format: 2022-02-01T23:59:59Z')
@click.option('-f', '--from-mailbox', required=True, type=int,
              help='HelpScout mailbox id, use https://api.helpscout.net/v2/mailboxes endpoint')
@click.option('-t', '--to-mailbox', required=True, type=int,
              help='FreeScout mailbox id, you can see it with browser in https://hs.somenergia.coop/mailbox/<mailbox_id> url')

def main(**kwargs):
    erp_emails = read_csv_emails(EMAIL_FILENAME)

    hs_mailbox = kwargs.get('from_mailbox', False)
    fs_mailbox = kwargs.get('to_mailbox', False)
    start_date = kwargs.get('start_date', False)
    end_date = kwargs.get('end_date', False)

    url = f'https://api.helpscout.net/v2/conversations?mailbox={hs_mailbox}&embed=threads&query=(createdAt:[{start_date} TO {end_date}] AND tag:(NOT "nagios" AND NOT "fail2ban" AND NOT "backups"))&status=all'

    pbar, page_size = get_tqdm(url)
    next_url = url
    while next_url:
        response = requests.get(next_url, headers=HS_HEADERS)

        if response.status_code == 200:
            data = response.json()

            for item in data['_embedded']['conversations']:
                if newer_than_4y(item.get("createdAt")) or customer_email_in_erp(item, erp_emails):
                    create_conversation(hs_conversation=item, fs_mailbox=fs_mailbox)
                else:
                    print(f'{item.get("id", "")} not migrated')
            pbar.update(page_size)
            next_url = data['_links'].get('next', dict()).get('href')
        else:
            print(f'Error in request: {response.status_code}')
            print(response.text)
    pbar.close()


if __name__ == '__main__':
    main()
