#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configdb

from consolemsg import step, error, warn, fail, success
from erppeek import Client
from stdnum.es import referenciacatastral as evalrefcatastral


def fix_incoherent_cadastral_ref():
    '''
    Checks for incorrect cadastral reference format:
    in case of incorrect format, update it to a blank value.
    '''
    erp_client = Client(**configdb.erppeek)
    gcp_obj = erp_client.GiscedataCupsPs
    id_cups_list = gcp_obj.search([("active", "=", True)])
    n = 0    
    for id_cups in id_cups_list:
        cadastral_ref = gcp_obj.read(id_cups, ["ref_catastral"])["ref_catastral"]
        try:
            incoherent_cadastral_ref = evalrefcatastral.validate(cadastral_ref)
        except:
            if cadastral_ref: 
                gcp_obj.write(id_cups, {"ref_catastral": ""})
                n += 1
    success("{} incoherent cadastral references fixed", n)


if __name__ == '__main__':

    step("Find if cadastral reference has the proper format")
    try:
        fix_incoherent_cadastral_ref()
    except:
        error("Something went wrong... check fix_ref_catastral.py")
