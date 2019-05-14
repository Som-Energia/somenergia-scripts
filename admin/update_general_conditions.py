# -*- coding: utf-8 -*-
from threading import Semaphore
from concurrent import futures
from consolemsg import step, success, error, warn
from erppeek import Client
import configdb


MAX_WORKERS = configdb.MAX_CONC

LANG_DICT = {
    'es_ES': 'condicions_generals_som_01_es',
    'ca_ES': 'condicions_generals_som_01_ca',
    'gl_ES': 'condicions_generals_som_01_ga',
    'eu_ES': 'condicions_generals_som_01_ek',
}

erp_client = Client(**configdb.erppeek)

step("Connecting to: {}".format(erp_client._server))

Polissa = erp_client.model('giscedata.polissa')
CondicionsGenerals = erp_client.model('giscedata.polissa.condicions.generals')
IrModelData = erp_client.model('ir.model.data')


def get_general_condition(lang):
    condicions_lang_id = IrModelData.get_object_reference(
        'som_polissa_condicions_generals', LANG_DICT.get(lang, 'condicions_generals_som_01_es')
    )[1]

    return CondicionsGenerals.browse(condicions_lang_id)


def set_general_condition(polissa, sem):
    step("Setting general conditions for contract: {}".format(polissa.name))
    conditions = get_general_condition(polissa.titular.lang)
    with sem:
        try:
            polissa.condicions_generals_id = conditions
            res = True, polissa.name
        except Exception as e:
            msg = "An error ocurred setting general conditions for "\
                  "contract {}, reason: {}"
            error(msg.format(polissa.name, str(e)))
            res = False, polissa.name

    return res


def update_general_conditions():
    res = []
    sem = Semaphore()

    polissa_list = Polissa.browse(
        [('condicions_generals_id', '=', False)],
        0, 0, False, 
        {'active_test': False}
    )
    step("There are {} polissas to update".format(len(polissa_list)))

    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        to_do = [
            executor.submit(set_general_condition, polissa, sem)
            for polissa in polissa_list
        ]
        for task in futures.as_completed(to_do):
            try:
                res.append(task.result())
            except Exception as e:
                msg = "An error ocurred task {}, reason: {}"
                error(msg.format(task, str(e)))
    return res


def main():
    res = update_general_conditions()
    failed_contracts = [contract for contract in res if not contract[0]]
    if failed_contracts:
        contract_list = [contract[1] for contract in res]
        msg = "Achtung!! There folowing contracts failed:\n - {}"
        warn(msg.format(", ".join(contract_list)))

    success("Updated {} contracts".format(str(len(res))))


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemError):
        success("Chao!")
