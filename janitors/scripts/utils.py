#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, io, os
from dbutils import nsList
import psycopg2
import configdb


def get_data_from_erp(queryfile):

    with io.open(queryfile) as f:
        query = f.read()
    db = psycopg2.connect(**configdb.psycopg)
    with db.cursor() as cursor :
        try:
            cursor.execute(query)
        except KeyError as e:
            fail("Missing variable '{key}'. Specify it in the YAML file or by using the --{key} option"
                .format(key=e.args[0]))
        erp_data =  nsList(cursor)
    return erp_data
