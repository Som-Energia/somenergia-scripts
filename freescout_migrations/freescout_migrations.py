# -*- coding: utf-8 -*-

import requests
from configdb import URL, SECRET_KEY, MAILBOX_DESTINATION, HS_TOKEN

HS_HEADERS = {
    'Authorization': f'Bearer {HS_TOKEN}',
    'Content-Type': 'application/json'
}

FS_HEADERS = {
    "X-FreeScout-API-Key": SECRET_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def create_conversation(hs_conversation):
    request_url = "{}{}".format(URL, 'conversations')

    threads = []
    for th in hs_conversation['_embedded']['threads']:
        thread = {
            "type": th['type'],
            "user": 1,  # TODO: Maping
            "imported": True,
            "createdAt": th['createdAt']
        }
        if 'body' in th:
            thread['text'] = th['body']
        if th['type'] == 'customer':
            thread['cc'] = th['cc']
            thread['bcc'] = th['bcc']
            thread['customer'] = {'email': th['createdBy']['email']}
            thread['createdAt'] = th['createdAt']
        thread['attachments'] = []
        for attach in th['_embedded']['attachments']:
            attachment_ref = attach['_links']['data']['href']
            attachment_response = requests.get(url=attachment_ref, headers=HS_HEADERS)
            if attachment_response.status_code == 200:
                thread['attachments'].append({
                    "fileName": attach['filename'],
                    "mimeType": attach['mimeType'],
                    "data": attachment_response.json()['data']
                })
            else:
                print("Problem getting attachment")

        threads.append(thread)

    body = {
        "type": hs_conversation['type'],
        "mailboxId": MAILBOX_DESTINATION,
        "subject": hs_conversation['subject'],
        "customer": {
            "email": hs_conversation['primaryCustomer']['email'],
            "firstName": hs_conversation['primaryCustomer']['first'],
            "lastName": hs_conversation['primaryCustomer']['last']
        },
        "threads": threads,
        "imported": True,
        "assignTo": 1,  # TODO: Maping
        "status": hs_conversation['status'],
        "createdAt": hs_conversation['createdAt']
    }

    if hs_conversation['status'] == 'closed':
        body['closedAt'] = hs_conversation['closedAt']

    r = requests.post(request_url, json=body, headers=FS_HEADERS)

    print(r.status_code)


if __name__ == '__main__':
    mailbox = 249427  # Technocuca, mirar https://api.helpscout.net/v2/mailboxes
    start_date = '2023-01-01T00:00:00Z'
    end_date = '2023-05-31T23:59:59Z'

    url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&embed=threads&query=(createdAt:[{start_date} TO {end_date}])&status=all'

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
