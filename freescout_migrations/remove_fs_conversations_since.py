# -*- coding: utf-8 -*-
import click
import csv
import requests
from configdb import URL, SECRET_KEY, HS_TOKEN, EMAIL_FILENAME
from create_conversation import create_conversation
from tqdm import tqdm
from migration_checks import customer_email_in_erp, newer_than_4y


FS_HEADERS = {
    "X-FreeScout-API-Key": SECRET_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

POST_CONVERSATION_URL = "{}{}".format(URL, 'conversations')


@click.command()
@click.option('-s', '--start-date', required=True,
              help='Format: 2022-02-01T23:59:59Z')
@click.option('-m', '--mailbox_id', required=True, type=int,
              help='FreeScout mailbox id, you can see it with browser in https://hs.somenergia.coop/mailbox/<mailbox_id> url')

def main(**kwargs):
    mailbox_id = kwargs.get('mailbox_id', False)
    start_date = kwargs.get('start_date', False)

    url = f'https://freescout.somenergia.coop/api/conversations?mailboxId={mailbox_id}&createdSince={start_date}'

    response = requests.get(url, headers=FS_HEADERS)
    if response.status_code != 200:
        print("Error with first request")
        return

    total_pages = response.json().get('page', {}).get('totalPages')
    pbar = tqdm(total=response.json().get('page', {}).get('totalElements'))
    page_size = response.json().get('page', {}).get('size')
    for page in range(1, total_pages + 1):
        url = f'https://freescout.somenergia.coop/api/conversations?mailboxId={mailbox_id}&createdSince={start_date}&page={page}'
        response = requests.get(url, headers=FS_HEADERS)

        if response.status_code == 200:
            data = response.json()

            for conversation in data['_embedded']['conversations']:
                conversation_id = conversation.get('id')
                requests.delete(
                    url=f'https://freescout.somenergia.coop/api/conversations/{conversation_id}',
                    headers=FS_HEADERS
                )
            pbar.update(page_size)
        else:
            print(f'Error in request: {response.status_code}')
            print(response.text)
    pbar.close()


if __name__ == '__main__':
    main()
