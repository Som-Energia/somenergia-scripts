# -*- coding: utf-8 -*-
from threading import Semaphore
from concurrent import futures
from consolemsg import step, success, error, warn
from erppeek import Client
import configdb

MAX_ELEMS = 10  # Max elems to apply the validation
MAX_WORKERS = 5  # Max threads requesting acctions to the ERP server

erp_client = Client(**configdb.erppeek)


def validate_account_move(draft_move_ids, sem):
    '''
    draft_move_ids: list of ids to apply the validation acctions
    sem: semaphore to control how many validations can be done at the same time
    '''
    with sem:
        step("Validating account_move for ids: {}".format(draft_move_ids))
        res = erp_client.AccountMove.button_validate(draft_move_ids)

    return res


def get_draft_moves_ids(state, from_date, to_date):

    return erp_client.AccountMove.search([
        ('state', '=', state),
        ('date', '>=', from_date),
        ('date', '<=', to_date)
    ])


def validate_moves(draft_move_ids_list):
    '''
    draft_move_ids_list: Iterable of lists of move ids to validate
    '''
    res = {}
    sem = Semaphore()

    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        to_do = {
            executor.submit(validate_account_move, move_ids, sem): move_ids
            for move_ids in draft_move_ids_list
        }
        for task in futures.as_completed(to_do):
            try:
                res[to_do[task]] = task.result()
            except Exception as e:
                msg = "An error ocurred validating acount move with "\
                      "id {}, reason: {}"
                error(msg.format(to_do[task], str(e)))
                res[to_do[task]] = False
    return res


def main():
    state = 'draft'
    from_date = '2017-01-01'
    to_date = '2017-12-31'

    step("Getting drafts moves")
    draft_move_ids = get_draft_moves_ids(state, from_date, to_date)

    step("There are {} account moves to validate".format(len(draft_move_ids)))
    if draft_move_ids:
        step("Do you want to continue? (Y/n)")
        answer = raw_input()
        while answer.lower() not in ['y', 'n', '']:
            answer = raw_input()
            step("Do you want to continue? (Y/n)")
        if answer in ['n', 'N']:
            raise KeyboardInterrupt

    draft_move_ids_gen = (
        tuple(draft_move_ids[i:i + MAX_ELEMS])
        for i in range(0, len(draft_move_ids), MAX_ELEMS)
    )
    res = validate_moves(draft_move_ids_gen)
    failed = {
        move_ids: result for move_ids, result in res.iteritems() if result is False
    }
    while failed:
        warn("There were failed validation, tring again")
        res = validate_moves(failed)
        failed = {
            elem: result for elem, result in res.iteritems() if result is False
        }

    success("Done!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        success("Chao!")
