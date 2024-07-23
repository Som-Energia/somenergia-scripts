# -*- coding: utf-8 -*-

import requests
from configdb import URL, SECRET_KEY, HS_TOKEN
from create_conversation import create_conversation
from tqdm import tqdm


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


if __name__ == '__main__':
    mailbox = 187926  # Mirar https://api.helpscout.net/v2/mailboxes
    start_date = '2010-01-01T00:00:00Z'
    end_date = '2025-01-01T23:59:59Z'

    url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&embed=threads&query=(createdAt:[{start_date} TO {end_date}] AND tag:(NOT "nagios" AND NOT "fail2ban" AND NOT "backups"))&status=all'

    pbar, page_size = get_tqdm(url)
    next_url = url
    while next_url:
        response = requests.get(next_url, headers=HS_HEADERS)

        if response.status_code == 200:
            data = response.json()

            for item in data['_embedded']['conversations']:
                create_conversation(hs_conversation=item)
            pbar.update(page_size)
            next_url = data['_links'].get('next', dict()).get('href')
        else:
            print(f'Error in request: {response.status_code}')
            print(response.text)
    pbar.close()