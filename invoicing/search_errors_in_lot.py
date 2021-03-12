#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
reload(sys) # dirty hack for the underlay script
sys.setdefaultencoding('utf8')

from erppeek import Client
import configdb
from yamlns import namespace as ns
from consolemsg import step, success
import StringIO
import csv


def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
        )
    return parser.parse_args(namespace=ns())


filename = parseArguments().output

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

# Objectes
pol_obj = O.GiscedataPolissa
lot_obj = O.GiscedataFacturacioLot
clot_obj = O.GiscedataFacturacioContracte_lot
w_obj = O.GiscedataFacturacioValidationWarningTemplate

open_lot_ids = lot_obj.search([("state", "=", "obert")])

fact_inc_ids = clot_obj.search([
                                    ('lot_id', 'in', open_lot_ids),
                                    ('state', '=', 'facturat_incident'),
                                ])

error_codes = sorted(w_obj.read(w_obj.search(), 'code'))

header = []
header.extend([
    'Polissa',
    'autoconsum',
    'factura_per',
    'distri',
    ])
header.extend(error_codes)
header.extend([
    'errors_totals',
    'text_error',
    ])

report = [header]

FX01_i_str = "Data inici de la factura: "
FX01_m_str = ", data final: "
FX01_f_str = ", número de lectures"

for counter, fact_inc_id in enumerate(fact_inc_ids):
    data = []
    report.append(data)

    clot = clot_obj.browse(fact_inc_id)

    success("{}/{} llegint per polissa {}",
            counter+1, len(fact_inc_ids), clot.polissa_id.name)
    data.append(clot.polissa_id.name)

    step("Autoconsum: {}", clot.polissa_id.autoconsumo)
    data.append(clot.polissa_id.autoconsumo)

    step("Factura per: {}", clot.polissa_id.facturacio_potencia)
    data.append(clot.polissa_id.facturacio_potencia)

    step("Distri: {}", clot.polissa_id.distribuidora.name)
    data.append(clot.polissa_id.distribuidora.name.replace(",", " "))

    errors = 0
    for error_code in error_codes:
        if error_code in clot.status:
            step("error de validacio: {}", error_code)
            data.append('1')
            errors += 1
        else:
            data.append(' ')

    step("Errors totals: {}", errors)
    data.append(errors)

    step("Text: {}", clot.status)
    data.append(clot.status)

csv_doc = StringIO.StringIO()
writer_report = csv.writer(csv_doc, delimiter=';')
writer_report.writerows(report)
doc = csv_doc.getvalue()
with open(filename, 'w') as f:
    f.write(doc)

# vim: et ts=4 sw=4
