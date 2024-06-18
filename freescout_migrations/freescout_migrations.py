# -*- coding: utf-8 -*-

import requests
from configdb import URL, SECRET_KEY, MAILBOX_DESTINATION, HS_TOKEN, USER_MAPPING

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

def create_conversation(hs_conversation):
    try:
        threads = []
        for th in hs_conversation['_embedded']['threads']:
            thread = {
                "type": th['type'],
                "imported": True,
                "createdAt": th['createdAt']
            }
            if th['type'] != 'customer':
                thread["user"] = USER_MAPPING[th['createdBy']['id']]
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
                "email": hs_conversation['primaryCustomer'].get('email', ""),
                "firstName": hs_conversation['primaryCustomer'].get('first', ""),
                "lastName": hs_conversation['primaryCustomer'].get('last', ""),
            },
            "threads": threads,
            "imported": True,
            "status": hs_conversation['status'],
            "createdAt": hs_conversation['createdAt']
        }
        if 'assignee' in hs_conversation:
            body['assignTo'] = USER_MAPPING[hs_conversation['assignee']['id']]
        if hs_conversation['status'] == 'closed':
            body['closedAt'] = hs_conversation['closedAt']
        fs_tags = []
        if 'tags' in hs_conversation:
            for tag in hs_conversation['tags']:
                fs_tags.append(tag['tag'])

        response = requests.post(POST_CONVERSATION_URL, json=body, headers=FS_HEADERS)

        if response.status_code != 201:
            print(response.status_code, hs_conversation.get('subject', ""), hs_conversation.get('id', ""))
        elif fs_tags:
            response_tags = requests.put(ADD_TAGS_URL.format(response.json()['id']), json={'tags': fs_tags}, headers=FS_HEADERS)
            if response_tags.status_code != 204:
                print("Tag Error: ", response_tags.status_code, hs_conversation['subject'])

    except Exception as e:
        print("No he pogut gestionar:", hs_conversation.get('subject', ""), hs_conversation.get('id', ""))
        print(e)



if __name__ == '__main__':
    mailbox = 249427  # Technocuca, mirar https://api.helpscout.net/v2/mailboxes
    start_date = '2010-03-04T00:00:00Z'
    end_date = '2025-03-04T23:59:59Z'

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
