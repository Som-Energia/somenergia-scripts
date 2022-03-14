#from concurrent.futures import ThreadPoolExecutor, wait
# concurrent no està disponible per python 3?
# han fet un backport per python3 https://pypi.org/project/futures/
from calendar import c
from concurrent.futures import ThreadPoolExecutor, wait
import sys
import os.path
import datetime
import zipfile
import traceback
import argparse
import requests
import pandas as pd
from configdb import apinergia
from consolemsg import error, step, success
from functools import reduce
import pytz

BASE_URL = apinergia['server']
USERNAME = apinergia['user']
PASSWORD = apinergia['password']

BASE_PATH = apinergia.get('csv_output_directory', '/tmp')

accepted_curve_types = [
    'tg_cchfact',
    'tg_cchval',
    'tg_f1',
    'P1',
    'P2',
    'tg_cchautoconsum',
    'tg_gennetabeta',
]

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

# TODO remove this patch once the backend is fixed and times are correct
# currently it is returning one hour less than it should
def bugfix_add_one_hour(df_column):
    df_column = df_column + pd.Timedelta(hours=1)
    return df_column


def cch_json_to_dataframe(results, cch_type, from_date, to_date):
    columns = ('contractId','meteringPointId') + tuple(results[0]['measurements'].keys())

    llista_measurements = [(r['contractId'],r['meteringPointId'],*tuple(r['measurements'].values())) for r in results]
    measurements = pd.DataFrame(llista_measurements, columns = columns)

    # TODO remove this workaround once backend is patched and uncomment the original line below
    measurements['date'] = bugfix_add_one_hour(pd.to_datetime(measurements['date']))
    measurements['date'] = measurements['date'].dt.tz_convert("Europe/Madrid")
    #measurements['date'] = pd.to_datetime(measurements['date']).dt.tz_convert("Europe/Madrid")

    # ugly reordering
    dates = measurements['date']
    measurements = measurements.drop(columns=['date'])
    measurements.insert(loc=1, column='date', value=dates)

    measurements['dateUpdate'] = pd.to_datetime(measurements['dateUpdate'])
    # TODO we will fuck up if there's more than one meteringPoint (it will pick one at random by dateUpdate)
    measurements = measurements.loc[measurements.groupby(["date","meteringPointId"])['dateUpdate'].idxmax()] # filtering deprecated values
    measurements = measurements.set_index(['date','meteringPointId'], drop=False)
     
    timezone = pytz.timezone('Europe/Madrid')

    meterings = measurements['meteringPointId'].unique()
    nmeterings = len(meterings)
    date_range = pd.date_range(timezone.localize(from_date), timezone.localize(to_date), freq='H')
    
    date_range = date_range.repeat(nmeterings)
    #meterings = meterings.repeat(len(date_range))
    meterings = [[m] for m in meterings] * int(len(date_range) / nmeterings)
    meterings = [item for sublist in meterings for item in sublist]

    measurements = measurements.reindex([date_range, meterings])

    measurements = measurements\
        .add_prefix(cch_type + '_')\
        .rename(columns={
            cch_type + '_date':'date',
            cch_type + '_contractId':'contractId'
            }
        )
    
    measurements = measurements.reset_index(drop = True)

    return measurements


def df_to_csv(df, contract_id, cch_type, from_date, to_date):
    filename = '{}/CCH_download_{}_{}_{}_{}.csv'.format(BASE_PATH, from_date, to_date, cch_type, contract_id)
    df.to_csv(filename, sep=';', index=False)
    return filename

def get_cch_curves_csv(contract, cch_types, from_date, to_date):

    from_date_excess_dt = datetime.datetime.strptime(from_date, "%Y-%m-%d") - datetime.timedelta(days=1)
    from_date_excess = datetime.datetime.strftime(from_date_excess_dt, "%Y-%m-%d")

    to_date_excess_dt = datetime.datetime.strptime(to_date, "%Y-%m-%d") + datetime.timedelta(days=1)
    to_date_excess = datetime.datetime.strftime(to_date_excess_dt, "%Y-%m-%d")

    cchs = []
    for cch_type in cch_types:
        cch_json = get_cch_curves(contract, cch_type, from_date_excess, to_date_excess)
        if not cch_json:
            print("Contract {} without curves of type {}.".format(contract, cch_type)) 
            continue

        cchs.append((cch_type, cch_json_to_dataframe(cch_json, cch_type, from_date_excess_dt, to_date_excess_dt)))

    if not cchs:
        return

    all_types_curves_df = pd.DataFrame(columns=['date', 'contractId'])
    print('Merging {} curves'.format(len(cchs)))
    for cch_type, curve_df in cchs:
        all_types_curves_df = pd.merge(all_types_curves_df, curve_df, on=['date', 'contractId'], how='outer', sort=False)
    
    all_types_curves_df = truncate_date_range(all_types_curves_df, from_date, to_date)

    csv_filename = df_to_csv(all_types_curves_df, contract, cch_type, from_date, to_date)
    # errors are handled via exceptions
    return csv_filename

def truncate_date_range(df, from_date, to_date):

    # be conscious that timedelta additions are not aware of timezone changes and DST
    # In [66]: (pytz.timezone('Europe/Madrid').localize(datetime.datetime(2022,3,27,3))).isoformat()
    # Out[66]: '2022-03-27T03:00:00+02:00'
    # In [67]: (pytz.timezone('Europe/Madrid').localize(datetime.datetime(2022,3,27,2))+datetime.timedelta(hours=1)).isoformat()
    # Out[67]: '2022-03-27T03:00:00+01:00'

    timezone = pytz.timezone('Europe/Madrid')
    from_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").astimezone(timezone)
    to_date = timezone.localize(datetime.datetime.strptime(to_date, "%Y-%m-%d")) + datetime.timedelta(days=1)
    return df[(from_date < df['date']) & (df['date'] <= to_date)]

def get_contracts_cch_csv(contract_type_list):
    results = dict()
    with ThreadPoolExecutor(max_workers=20) as executor:
        tasks = {
            executor.submit(get_cch_curves_csv, contract, cch_types, from_date, to_date): contract
            for contract, cch_types, from_date, to_date in contract_type_list
        }
        todo = tasks

        while todo:
            done, todo = wait(todo, timeout=10)
            for task in done:
                results[tasks[task]] = task.result()
                print(tasks[task])

    return results

def main(contracts, curve_types, from_date, to_date, output_file):

    curve_types = [x.strip() for x in curve_types.split(',')]
    
    contracts = [x.strip() for x in contracts.split(',')]
     
    contract_type_list = [(contract, curve_types, from_date, to_date) for contract in contracts]

    # Example:
    #contract_type_list = [('0173713', 'tg_cchfact', '2021-12-16', '2021-12-17')]
    # tg_cchfact
    # tg_cchval
    # contract_type_list = [
    #     ('0042625','tg_cchfact','2021-01-01','2022-02-02'),
    #     ('0042639','tg_cchfact','2021-01-01','2022-02-02'),
    #     ('0042640','tg_cchfact','2021-01-01','2022-02-02'),
    #     ('0042646','tg_cchfact','2021-01-01','2022-02-02'),
    #     ('0173713','tg_cchfact','2021-01-01','2022-02-02'),
    #     ('0173714','tg_cchfact','2021-01-01','2022-02-02'),
    #     ('0173715','tg_cchfact','2021-01-01','2022-02-02'),
    #     ('0173716','tg_cchfact','2021-01-01','2022-02-02')
    # ]

    results = get_contracts_cch_csv(contract_type_list)

    # zip results
    zipfilename = output_file
    # zipfilename = "{}/cch_download.zip".format(BASE_PATH, datetime.datetime.now().isoformat())
    with zipfile.ZipFile(zipfilename, 'w') as archive:
        
        for filename in results.values():
            if filename:
                archive.write(filename, os.path.basename(filename))

    print(results)

    print("csv cch files saved in {}".format(zipfilename))


# CCh's tipo P5D; F5D; A5D; B5D
# (CCH_VAL; CCH_FACT; CCH_AUTOCONSUM; CCH_GENNETABETA)
# periodo: 01/01/2021 hasta 01/02/2022

# contractes = ['0042625','0042639','0042640','0042646','0173713','0173714','0173715','0173716']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Elsxutu korbojn kaj fek vi'
    )

    parser.add_argument(
        '--contracts',
        dest='contracts',
        required=True,
        help="Números de contractes de 7 digits separats per comes (e.g. 0731234, 1230923)"
    )

    parser.add_argument(
        '--from_date',
        dest='from_date',
        required=True,
        help="Introdueix la data d'inici del perídode que cal decarregar 'YYYY-mm-dd'"
    )

    parser.add_argument(
        '--to_date',
        dest='to_date',
        required=True,
        help="Introdueix la data final del perídode que cal decarregar 'YYYY-mm-dd'"
    )

    parser.add_argument(
        '--curve_types',
        dest='curve_types',
        required=True,
        help="Tipus de corba e.g. (tg_cchva o bé tg_cchfact...)"
    )

    parser.add_argument(
        '--output',
        dest='output_file',
        required=True,
        help="Fitxer de sortida amb els resultats"
    )

    args = parser.parse_args()
    try:
        main(args.contracts, args.curve_types, args.from_date, args.to_date, args.output_file)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El procés no ha finalitzat correctament: {}", str(e))
    else:
        success("Job's Done, Have A Nice Day")

