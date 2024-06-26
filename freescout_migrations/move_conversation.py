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

    conversation_id = 1990925049  # TODO: Script input
    url = f'https://api.helpscout.net/v2/conversations/{conversation_id}?embed=threads&status=all'

    response = requests.get(url, headers=HS_HEADERS)

    if response.status_code == 200:
        create_conversation(hs_conversation=response.json())
    else:
        print(f'Can\'t move conversation: {response.status_code}')
        print(response.text)
