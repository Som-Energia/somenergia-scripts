#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, configdb

from consolemsg import step, error, warn, fail, success
from erppeek import Client
from utils import get_data_from_erp

def fix_members_without_entry():
    '''
    Finds those members with Client entry, member category and
    SXXXXXX like code which doesn't have entry in somenergia_soci
    and creates them.
    '''
    erp_client = Client(**configdb.erppeek)

    ROOT_DIR = os.path.dirname(os.getcwd())
    queryfile = ROOT_DIR + "/sql/find_members_without_entry.sql"
    data = get_data_from_erp(queryfile)

    soci_obj = erp_client.SomenergiaSoci
    id_list = [elem.id for elem in data]

    try:
        id_socis_list = soci_obj.create_socis(id_list)
    except Exception as e:
        error("An error has occurred creating Members, {}", e)
    else:
        success("Following Member id's were created {} ", id_socis_list)


if __name__ == '__main__':

    step("Starting...")
    try:
        fix_members_without_entry()
    except Exception as e:
        error("Something went wrong {}", e)

