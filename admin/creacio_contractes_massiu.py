#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from openpyxl import load_workbook

uri = 'https://api.somenergia.coop/form/contractacio'
#uri='http://testing.somenergia.coop:5001/form/contractacio'

def add_contract(data):
    import requests
    r = requests.post(uri, data=data)
    return (r.status_code, r.reason, r.text)

def crea_contractes(filename = None):
    if not filename:
        sys.exit("No hi ha cap arxiu per crear contractes")
    wb = load_workbook(filename)
    ws = wb.active
    valors = []
    keys = []
    pols = []
    column = 1
    while ws.cell(row=1,column=column).value:
        keys.append(ws.cell(row=1,column=column).value)
        column += 1
    row=2
    while ws.cell(row=row,column=1).value:
        column = 1
        valors = []
        while ws.cell(row=1,column=column).value:
            valors.append(ws.cell(row=row,column=column).value)
            column += 1
        pols.append(dict(zip(keys,valors)))
        row+=1 
    for pol in pols:
        print pol['cups']
        status,reason, text = add_contract(pol)
        print 'Status: ' + str(status)
        print 'Reason: ' + str(reason)
        print 'Text: ' + str(text)
        

crea_contractes(filename=sys.argv[1])

