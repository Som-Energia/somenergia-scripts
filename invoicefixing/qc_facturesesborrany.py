#!/usr/bin/env python
#-*- coding: utf8 -*-

import psycopg2
import dbutils
import sys
from consolemsg import step, error, fail, warn
from yamlns import namespace as ns
import os

template="""\
Validació de Factures en Esborrany del lot
==========================================

(Las facturas cuya última lectura facturada es real son dadas por válidas
 y no aparecen en este listado)

- Factures en esborrany: {draft} 
- Import de les factures en esborrany: {draft_amount:.2f}€
- Amb imports de més de 5000: {bigger_than_5000} 
- Amb consums més grans que el que permet la potència: {sobre_consum} 
- Amb consums més grans que el 50% del que permet la potència: {sobre_consum_50} 
- Amb R1 oberts: {r1_obert} 
- Factures de zero dies: {zero_days} 
- Factures sense linies de energia: {zero_lines}

Detall (números de pòlisses):

- Amb imports de més de 5000: {bigger_than_5000_ids} 
- Amb consums més grans que el que permet la potència: {sobre_consum_ids} 
- Amb consums més grans que el 50% del que permet la potència: {sobre_consum_50_ids} 
- Amb R1 oberts: {r1_obert_ids} 
- Factures de zero dies: {zero_days_ids} 
- Factures sense linies de energia: {zero_lines_ids} 

"""

def main():
    options = ns()
    optarg = None
    cliargs = ns()
    keyarg = None
    args = []
    for arg in sys.argv[1:]:
        if keyarg:
            cliargs[keyarg]=eval(arg) if arg.startswith("(") else arg
            keyarg=None
            continue
        if optarg:
            options[optarg]=arg
            optarg=None
            continue
        if arg.startswith('--'):
            keyarg = arg[2:]
            continue
        if arg.startswith('-'):
            optarg = arg[1:]
            continue
        args.append(arg)
    """
    if not args:
        fail("Argument required. Usage:\n"
        "{} <sqlfile> [-C <dbconfig.py>] [<yamlfile>] [--<var1> <value1> [--<var2> <value2> ..] ]".format(sys.argv[0]))
    """

    sqlfilename = os.path.join(os.path.dirname(__file__), "draftinvoices.sql")

    step("Loading {}...".format(sqlfilename))
    with open(sqlfilename) as sqlfile:
        query = sqlfile.read()
    

    if 'C' in options:
        import imp
        config=imp.load_source('config',options.C)
    else:
        import config

    step("Connecting to the database...")
    db = psycopg2.connect(**config.psycopg)

    with db.cursor() as cursor :
        try:
            cursor.execute(query)
        except KeyError as e:
            fail("Missing variable '{key}'. Specify it in the YAML file or by using the --{key} option"
                .format(key=e.args[0]))
        print template.format(**dbutils.nsList(cursor)[0])

main()




