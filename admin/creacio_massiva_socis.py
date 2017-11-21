#!/usr/bin/env python
# -*- coding: utf-8 -*-  
from creacio_socis import format_yaml
import os, fnmatch
import sys

def list_files(path, date):
    listOfFiles = os.listdir(path)
    pattern = '%s*alta.yaml' % date
    for entry in listOfFiles:
        if fnmatch.fnmatch(entry, pattern):
            format_yaml(entry)

if len(sys.argv) < 3:
    sys.exit("Cal indicar el path i la data 2017-11-10")

list_files(path=sys.argv[1], date=sys.argv[2])

# vim: et ts=4 sw=4
