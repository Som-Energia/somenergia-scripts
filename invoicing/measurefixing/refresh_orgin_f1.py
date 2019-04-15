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

wrong_attachments = []
bad_xml = []
updated = []

for count,f1line_id in enumerate(f1line_ids):
    io.step("{}/{} processing {}",count+1,f1line_len,f1line_id)

    f1line = f1line_obj.get(f1line_id)
    atachments = len(f1line._attachments_field)
    if atachments != 1:
        io.warn("detected {} atatchments!! skipping...",atachments)
        wrong_attachments.append(f1line_id)
        print "id {} detected {} attachments, skiped.".format(f1line_id,atachments)
        continue

    f1_b64 = f1line._attachments_field[0].datas_mongo
    f1_xml = base64.decodestring(f1_b64)
    f1_hits = re.findall('<NumeroFactura>.*</NumeroFactura>',f1_xml)
    if len(f1_hits) != 1:
        io.warn("detected {} hits searching the NumeroFactura tag in the xml!! skiping...",len(f1_hits))
        bad_xml.append(f1line_id)
        print "id {} detected {} hits in xml, skiped.".format(f1line_id,len(f1_hits))
        continue

    f1_number = f1_hits[0].replace('<NumeroFactura>','').replace('</NumeroFactura>','')
    io.step("number found: '{}'",f1_number)

    if doit:
        io.step("Writing!!!")
        f1line.write({'invoice_number_text':f1_number})
    updated.append(f1line_id)
    print "id {} updated with {}".format(f1line_id,f1_number)

io.info('Updated:')
io.info(' - {}',', '.join([str(i) for i in updated]))
io.info('')
io.info('With wrong attachemnts:')
io.info(' - {}',', '.join([str(i) for i in wrong_attachments]))
io.info('')
io.info('With bad xml:')
io.info(' - {}',', '.join([str(i) for i in bad_xml]))
print "updated:"
print updated
print "wrong attachemnts:"
print wrong_attachments
print "bad xml file:"
print bad_xml
