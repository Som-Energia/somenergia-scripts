# -*- coding: utf-8 -*-

import requests
from configdb import SECRET_KEY


def main():
    hs_url = 'https://api.helpscout.net/v2/users?email='
    hs_token = "YOU_TOKEN"  # Create it!
    hs_headers = {
        'Authorization': f'Bearer {hs_token}',
        'Content-Type': 'application/json'
    }

    fs_url = 'https://hs.somenergia.coop/api/users?pageSize=500'
    fs_token = SECRET_KEY
    fs_headers = {
        "X-FreeScout-API-Key": fs_token,
        'Content-Type': 'application/json'
    }

    relation_hs_fs = {}

    response = requests.get(fs_url, headers=fs_headers)

    if response.status_code == 200:
        data = response.json()

        for item in data['_embedded']['users']:
            hs_res = requests.get(hs_url+item['email'], headers=hs_headers)

            if hs_res.status_code == 200:
                hs_data = hs_res.json()
                if hs_data['_embedded']['users']:
                    relation_hs_fs[hs_data['_embedded']['users'][0]['id']] = item['id']
                else:
                    print(f"{item['email']} no trobat D:")
            else:
                print(f"Problema en crida {item['email']}")
    else:
        print(f'Error en la petición: {response.status_code}')
        print(response.text)


    print(relation_hs_fs)


if __name__ == '__main__':
    main()