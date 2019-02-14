#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbconfig; import ooop; O = ooop.OOOP(**dbconfig.ooop)
templates  = O.PoweremailTemplates.filter()

for template in templates:
    traduccions  = O.IrTranslation.filter(
        name='poweremail.templates,def_body_text',
        res_id=template.id,
    )
    trad_ca = None
    trad_es = None
    trad_en = None

    for trad in traduccions:
        if trad.lang == "ca_ES":
            trad_ca = trad
        if trad.lang == "es_ES":
            trad_es = trad
        if trad.lang == "en_US":
            trad_en = trad

    if trad_ca and trad_es and trad_en:
        print template.id, "OK :", template.name, ">>> Ja esta OK"

    if trad_ca:
        if trad_es is None:
            print "No te castella", str(template.id)
        if trad_en is None:
            print "No te angles", str(template.id)
            O.IrTranslation.create({
                       'lang':'en_US',
                       'src': trad_ca.src,
                       'name': trad_ca.name,
                       'type': trad_ca.type,
                       'res_id': trad_ca.res_id,
                       'value': trad_ca.value,
            })
    else:
        print template.id, "KO :", template.name, ">>> No l'hem pogut arreglar"

