import requests


def main():
    mailbox = # Technocuca, mirar https://api.helpscout.net/v2/mailboxes
    start_date = '2023-01-01T00:00:00Z'
    end_date = '2023-05-31T23:59:59Z'
    
    url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&embed=threads&query=(createdAt:[{start_date} TO {end_date}])&status=all'
    token = ''
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


    next_url = url
    while next_url:
        response = requests.get(next_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            
            for item in data['_embedded']['conversations']:
                print("Conversa: "+item['subject'])

                for thread in item['_embedded']['threads']:
                    if thread['type'] not in ['customer', 'message', 'note']:
                        continue
                    
                    print(f"-> Thread {thread['id']} de tipus {thread['type']}")

                    # mirem si te attachments:
                    for attach in thread['_embedded']['attachments']:
                        print(" => Te attachment "+attach['filename'])
                        # fer crida get autoritzada a attach['_links']['data']['href'] que retorna base64 del attachment



            next_url = data['_links'].get('next', dict()).get('href')
        else:
            print(f'Error in request: {response.status_code}')
            print(response.text)
    

if __name__ == '__main__':
    main()
