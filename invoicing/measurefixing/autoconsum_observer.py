#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import base64
from consolemsg import step, success, warn
from validacio_eines import lazyOOOP
from gestionatr.defs import TENEN_AUTOCONSUM
from gestionatr.input.messages.F1 import CODIS_AUTOCONSUM

tag = 'ConceptoRepercutible'
tag_head = '<'+tag+'>'
tag_tail = '</'+tag+'>'
tag_head_len = len(tag_head)
tag_tail_len = len(tag_tail)

Obj = lazyOOOP()

pol_obj = Obj.GiscedataPolissa
f1_obj = Obj.GiscedataFacturacioImportacioLinia

pol_ids = pol_obj.search([('autoconsumo', 'in', TENEN_AUTOCONSUM)])

for count,pol_id in enumerate(pol_ids):
    pol = pol_obj.browse(pol_id)

    last_pool = "No."
    if pol.comptadors and pol.comptadors[0].pool_lectures:
        last_pool = pol.comptadors[0].pool_lectures[0].name

    success("({}/{}) Polissa amb autoconsum {} , data ultima lectura facturada {} " +
            "i ultima lectura a pool {}",
            count+1,len(pol_ids),pol.name, pol.data_ultima_lectura, last_pool)

    f1_ids = f1_obj.search([('cups_id', '=', pol.cups.id)])
    if f1_ids:
        f1line = f1_obj.browse(f1_ids[0])
        step(" última importacio id {} feta el {} , fitxer F1 de {}",
             f1_ids[0], f1line.data_carrega, f1line.f1_date[:10])
        step(" {} fitxers adjunts, analitzant...",
             len(f1line._attachments_field))
        for attachment in f1line._attachments_field:
            f1_xml = base64.decodestring(attachment.datas_mongo)
            f1_hits = re.findall(tag_head + '..' + tag_tail, f1_xml)
            for f1_hit in f1_hits:
                tag_data = f1_hit[tag_head_len:-tag_tail_len]
                if tag_data in CODIS_AUTOCONSUM:
                    warn("Tag {} trobat amb valor {} dades autoconsum que " +
                         "indiquen --> {}",
                         tag, tag_data, CODIS_AUTOCONSUM[tag_data])

# vim: et ts=4 sw=4
