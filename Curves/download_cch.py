#from concurrent.futures import ThreadPoolExecutor, wait
# concurrent no està disponible per python 3?
# han fet un backport per python3 https://pypi.org/project/futures/
from concurrent.futures import ThreadPoolExecutor, wait
from configdb import apinergia
import requests
import pandas as pd
import datetime
import zipfile
import os.path

BASE_URL = apinergia['server']
USERNAME = apinergia['user']
PASSWORD = apinergia['password']

BASE_PATH = apinergia.get('csv_output_directory', '/tmp')

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
    columns = ('contractId','meteringPointId')+tuple(results[0]['measurements'].keys())
    llista_measurements = [(r['contractId'],r['meteringPointId'],*tuple(r['measurements'].values())) for r in results]
    measurements = pd.DataFrame(llista_measurements, columns = columns)
    measurements['date'] = pd.to_datetime(measurements['date']).dt.tz_convert("Europe/Madrid")
    measurements['dateUpdate'] = pd.to_datetime(measurements['dateUpdate'])
    measurements = measurements.loc[measurements.groupby(["date"])["dateUpdate"].idxmax()] # filtering deprecated values
    measurements = measurements.set_index('date', drop=False)
    date_range = pd.date_range(min(measurements['date']),max(measurements['date']), freq='H')
    measurements = measurements.reindex(date_range)
    return measurements

def df_to_csv(df, contract_id, cch_type, from_date, to_date):
    filename = '{}/CCH_download_{}_{}_{}_{}.csv'.format(BASE_PATH, from_date, to_date, cch_type, contract_id)
    df.to_csv(filename, sep=';', index=False)
    return filename

def get_cch_curves_csv(contract, cch_type, from_date, to_date):
    cch_json = get_cch_curves(contract, cch_type, from_date, to_date)
    if not cch_json:
        print("Contract {} without curves of type {}.".format(contract,cch_type)) 
        return None
        
    cch_df = cch_json_to_dataframe(cch_json)
    csv_filename = df_to_csv(cch_df, contract, cch_type, from_date, to_date)
    # errors are handled via exceptions
    return csv_filename

def get_contracts_cch_csv(contract_type_list):
    results = dict()
    with ThreadPoolExecutor(max_workers=20) as executor:
        tasks = {
            executor.submit(get_cch_curves_csv, contract, cch_type, from_date, to_date): contract
            for contract, cch_type, from_date, to_date in contract_type_list
        }
        todo = tasks

        while todo:
            done, todo = wait(todo, timeout=10)
            for task in done:
                results[tasks[task]] = task.result()
                print(tasks[task])

    return results

# Example:
#contract_type_list = [('0173713', 'tg_cchfact', '2021-12-16', '2021-12-17')]
# tg_cchfact
# tg_cchval
contract_type_list = [
	('0042625','tg_cchfact','2021-01-01','2022-02-02'),
	('0042639','tg_cchfact','2021-01-01','2022-02-02'),
	('0042640','tg_cchfact','2021-01-01','2022-02-02'),
	('0042646','tg_cchfact','2021-01-01','2022-02-02'),
	('0173713','tg_cchfact','2021-01-01','2022-02-02'),
	('0173714','tg_cchfact','2021-01-01','2022-02-02'),
	('0173715','tg_cchfact','2021-01-01','2022-02-02'),
	('0173716','tg_cchfact','2021-01-01','2022-02-02')
]


results = get_contracts_cch_csv(contract_type_list)

# zip results
zipfilename = "{}/{}_cch_download.zip".format(BASE_PATH, datetime.datetime.now().isoformat())
with zipfile.ZipFile(zipfilename, 'w') as archive:
    
    for filename in results.values():
        if filename:
            archive.write(filename, os.path.basename(filename))

print(results)

print("csv cch files saved in {}".format(zipfilename))

print("Job's Done, Have A Nice Day")



# CCh's tipo P5D; F5D; A5D; B5D
# (CCH_VAL; CCH_FACT; CCH_AUTOCONSUM; CCH_GENNETABETA)
# periodo: 01/01/2021 hasta 01/02/2022

# contractes = ['0042625','0042639','0042640','0042646','0173713','0173714','0173715','0173716']

