#from concurrent.futures import ThreadPoolExecutor, wait
# concurrent no està disponible per python 3?
# han fet un backport per python3 https://pypi.org/project/futures/
from concurrent.futures import ThreadPoolExecutor, wait
from configdb import apinergia
import requests
import pandas as pd

BASE_URL = apinergia['server']
USERNAME = apinergia['user']
PASSWORD = apinergia['password']


class Authentication:
    '''
    Clase para obtener el token de autenticación
    '''

    URL = f'{BASE_URL}/auth'

    @classmethod
    def get_token(cls, username, password):
        if not hasattr(cls, '_token'):
            response = requests.post(cls.URL, json={
                'username': username,
                'password': password
            })
            response.raise_for_status()
            cls._token = response.json()['access_token']
        return cls._token


def process_next_page(url, token):
    response = requests.get(
        url,
        headers={
            'accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    )
    try:
        response.raise_for_status()
    except Exception as e:
        return []

    results = response.json()['data']

    next_page = response.json().get('next_page')
    if next_page:
        results += process_next_page(next_page, token)

    return results


def get_cch_curves(contract, cch_type, start_date, end_date):
    # obtenemos el token de autenticación
    token = Authentication().get_token(USERNAME, PASSWORD)
    url = f'{BASE_URL}/cch/{contract}'
    response = requests.get(
        url,
        params={
            'type': cch_type,
            'from_': start_date,
            'to_': end_date,
            'limit': 15000
        },
        headers={
            'accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    )
    response.raise_for_status()
    results = response.json()['data']
    import pdb; pdb.set_trace()
    
    next_page = response.json().get('next_page')
    if next_page:
        results += process_next_page(next_page, token)

    return results


def get_contracts_cch(contract_list):
    results = dict()
    with ThreadPoolExecutor(max_workers=20) as executor:
        tasks = {
            executor.submit(get_cch_curves, contract, 'tg_cchfact', '2021-12-16', '2021-12-17'): contract
            for contract in contract_list
        }
        todo = tasks

        while todo:
            done, todo = wait(todo, timeout=10)
            for task in done:
                results[tasks[task]] = task.result()
                print(tasks[task])

    for result in results:
        with open(f'{result}.json', 'w') as output:
            json.dump(results[result], output)


def cch_json_to_dataframe(results):
    import pdb; pdb.set_trace()
    columns = ['contractId','meteringPointId','season', 'ai','ao','r1','r2','r3','r4','source','validated','date', 'dateDownload', 'dateUpdate']
    llista_measurements = [(r['contractId'],r['meteringPointId'],*tuple(r['measurements'].values())) for r in results]
    measurements = pd.DataFrame(llista_measurements, columns = columns)
    measurements['date'] = pd.to_datetime(measurements['date']).dt.tz_convert("Europe/Madrid")
    measurements = measurements.reset_index().set_index('date', drop=False)
    date_range = pd.date_range(min(measurements['date']),max(measurements['date']), freq='H')
    measurements = measurements.reindex(date_range)

    return pd.read_json(results)

results = get_cch_curves('0173713', 'tg_cchfact', '2021-01-01', '2021-01-02')
cch_json_to_dataframe(results)
