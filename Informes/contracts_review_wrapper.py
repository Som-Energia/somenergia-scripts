#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys) # dirty hack for the underlay script
sys.setdefaultencoding('utf8')

import os
import shutil
import datetime
import erppeek
import dbconfig
import tempfile
from consolemsg import step, fail
from yamlns import namespace as ns
from contracts_review import build
from zipfile import ZipFile
from os.path import basename


def getDateRange(start, end):
    start = datetime.datetime.strptime(start, "%Y-%m-%d")
    start_date = start.replace(day=1)

    end = datetime.datetime.strptime(end, "%Y-%m-%d")
    end_date = end.replace(day=1)
    end_date = (end_date + datetime.timedelta(days=32)).replace(day=1)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def getPartnerLang(partner):
    client = erppeek.Client(**dbconfig.erppeek)
    partner_obj = client.model('res.partner')
    partners_ids = partner_obj.search([('ref', '=', partner)])
    if not partners_ids:
        return None
    return partner_obj.read(partners_ids[0], ['lang'])['lang']


def wrapper(partner, start, end, output):
    start_date, end_date = getDateRange(start, end)
    partner_lang = getPartnerLang(partner)
    if not partner_lang:
        fail("Identificador de titular no trobat! {}", partner)

    tmp_dir = tempfile.mkdtemp()
    contractsfile = os.path.join(
        tmp_dir,
        "contracts_{}_{}.csv".format(partner, end_date))
    billsfile = os.path.join(
        tmp_dir,
        "invoices_{}_{}.csv".format(partner, end_date))

    step("start date ............ {}", start_date)
    step("end date .............. {}", end_date)
    step("partner ref ........... {}", partner)
    step("contracts file ........ {}", contractsfile)
    step("bills file ............ {}", billsfile)
    step("language .............. {}", partner_lang)
    build(
        start_date,
        end_date,
        partner,
        contractsfile,
        billsfile,
        lang=partner_lang)
    step("contract file ......... {}", contractsfile)
    step("invoices file ......... {}", billsfile)
    with ZipFile(output, 'w') as zipObj:
        zipObj.write(contractsfile, basename(contractsfile))
        zipObj.write(billsfile, basename(billsfile))
    step("zip file generated .... {}", output)
    shutil.rmtree(tmp_dir)


def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'partner',
        type=str,
        help="Partner",
        )
    parser.add_argument(
        'start',
        type=str,
        help="Date (isoformat)",
        )
    parser.add_argument(
        'end',
        type=str,
        help="Date (isoformat)",
        )
    parser.add_argument(
        'output',
        type=str,
        help="Output zip file",
        )
    return parser.parse_args(namespace=ns())


def main():
    args = parseArguments()
    print args
    wrapper(**args)


if __name__ == '__main__':
    main()

# vim: et ts=4 sw=4
