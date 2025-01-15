import requests
from configdb import SECRET_KEY, HS_TOKEN


def main():
    hs_url = 'https://api.helpscout.net/v2/users?page=4'
    hs_token = HS_TOKEN
    hs_headers = {
        'Authorization': f'Bearer {hs_token}',
        'Content-Type': 'application/json'
    }

    fs_url = 'https://hs.somenergia.coop/api/users'
    fs_token = SECRET_KEY
    fs_headers = {
        "X-FreeScout-API-Key": fs_token,
        'Content-Type': 'application/json'
    }

    response = requests.get(hs_url, headers=hs_headers)

    if response.status_code == 200:
        data = response.json()

        for item in data['_embedded']['users']:

            if item['type'] != 'user':
                continue

            post_res = requests.post(fs_url, headers=fs_headers, json={
                'firstName': item['firstName'],
                'lastName': item['lastName'],
                'email': item['email'],
                'jobTitle': item['jobTitle'],
                'phone': item['phone'],
                'timezone': item['timezone'],
            })

            if post_res.status_code == 201:
                print(f"{item['email']} creat correctament")
            else:
                print(f"Problema creant {item['email']}: {post_res.text}")
    else:
        print(f'Error en la petición: {response.status_code}')
        print(response.text)


if __name__ == '__main__':
    main()