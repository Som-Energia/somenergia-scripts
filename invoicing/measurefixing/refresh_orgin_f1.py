#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import re 
import base64
from validacio_eines import lazyOOOP
import consolemsg as io

O = lazyOOOP()
f1line_obj = O.GiscedataFacturacioImportacioLinia

doit = '--doit' in sys.argv

process_number = 100

filters = [('invoice_number_text','=',False)]

f1line_ids = f1line_obj.search(filters)
f1line_ids = f1line_ids[:process_number]
f1line_len = len(f1line_ids)

no_attachments = []
many_codes = []
updated = []

for count,f1line_id in enumerate(f1line_ids):
    io.step("{}/{} processing {}",count+1,f1line_len,f1line_id)

    f1line = f1line_obj.get(f1line_id)
    atachments = len(f1line._attachments_field)
    if atachments == 0:
        io.warn("detected {} atatchments!! skipping...",atachments)
        no_attachments.append(f1line_id)
        print "id {} detected {} attachments, skiped.".format(f1line_id,atachments)
        continue

    found_f1_codes = []
    for attachment in f1line._attachments_field:
        f1_xml = base64.decodestring(attachment.datas_mongo)
        f1_hits = re.findall('<NumeroFactura>.*</NumeroFactura>',f1_xml)
        for f1_hit in f1_hits:
            f1_number = f1_hit.replace('<NumeroFactura>','').replace('</NumeroFactura>','')
            if f1_number:
                found_f1_codes.append(f1_number)

    found_f1_codes = list(set(found_f1_codes))
    if len(found_f1_codes) != 1:
        io.warn("detected {} hits searching the NumeroFactura tag in the xmls!! skipping...",len(found_f1_codes))
        many_codes.append(f1line_id)
        print "id {} detected {} hits in xmls, skipped.".format(f1line_id,len(found_f1_codes))
        continue

    f1_number = found_f1_codes[0]
    io.step("number found: '{}'",f1_number)

    if doit:
        io.step("Writing!!!")
        f1line.write({'invoice_number_text':f1_number})
    updated.append(f1line_id)
    print "id {} updated with {}".format(f1line_id,f1_number)

io.info('Updated:')
io.info(' - {}',', '.join([str(i) for i in updated]))
io.info('')
io.info('With no attachemnts:')
io.info(' - {}',', '.join([str(i) for i in no_attachments]))
io.info('')
io.info('With too many codes:')
io.info(' - {}',', '.join([str(i) for i in many_codes]))
print "updated:"
print updated
print "no attachemnts:"
print no_attachments
print "too many codes:"
print many_codes
