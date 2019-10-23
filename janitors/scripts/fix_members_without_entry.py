#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, configdb

from consolemsg import step, error, warn, fail, success
from erppeek import Client
from utils import get_data_from_erp
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

def fix_members_without_entry():
    '''
    Finds those members with Client entry, member category and
    SXXXXXX like code which do not have entry in somenergia_soci
    and creates them.
    '''
    erp_client = Client(**configdb.erppeek)

    scriptsDir = Path(__file__).parent
    queryfile = scriptsDir.parent / "sql/find_members_without_entry.sql"

    data = get_data_from_erp(str(queryfile))

    soci_obj = erp_client.SomenergiaSoci
    id_partner_list = [elem.id for elem in data]

    step("Following Partner id's have no membership file {} ", id_partner_list)
    try:
        id_socis_list = soci_obj.create_socis(id_partner_list)
    except Exception as e:
        error("An error has occurred creating Members, {}", e)
    else:
        success("Following Member id's were created {} ", id_socis_list)


if __name__ == '__main__':

    step("Starting fix_members_without_entry")
    try:
        fix_members_without_entry()
    except Exception as e:
        error("Something went wrong {}", e)

