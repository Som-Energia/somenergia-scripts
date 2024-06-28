# -*- coding: utf-8 -*-

import requests
from configdb import URL, SECRET_KEY, HS_TOKEN
from create_conversation import create_conversation


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


if __name__ == '__main__':
    mailbox = 187923  # Technocuca, mirar https://api.helpscout.net/v2/mailboxes
    start_date = '2010-01-01T00:00:00Z'
    end_date = '2025-03-04T23:59:59Z'

    url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&embed=threads&query=(createdAt:[{start_date} TO {end_date}] AND tag:(NOT "nagios" AND NOT "fail2ban" AND NOT "backups"))&status=all'

    next_url = url
    while next_url:
        response = requests.get(next_url, headers=HS_HEADERS)

        if response.status_code == 200:
            data = response.json()

            for item in data['_embedded']['conversations']:
                create_conversation(hs_conversation=item)

            next_url = data['_links'].get('next', dict()).get('href')
        else:
            print(f'Error in request: {response.status_code}')
            print(response.text)
