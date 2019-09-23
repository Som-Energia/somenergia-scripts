#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import configdb
import base64
import time
from erppeek import Client
from consolemsg import step, success, warn
from subprocess import call

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

# variables
ids = [2190972]

# Helpers
def generate_pdf_ErpPeek(model, id):
    report_id = O.report(model, id)
    res = {'state': False}
    while not res['state']:
        res = O.report_get(report_id)
        time.sleep(0.2)

    return base64.b64decode(res['result'])

def generate_pdf_OOOP(model, id):
    from ooop import OOOP
    oo = OOOP(**configdb.ooop)
    return oo.report(model, [id])

def generate_inv_pdf(id):
    model = 'giscedata.facturacio.factura'

    #return generate_pdf_ErpPeek(model, id)
    return generate_pdf_OOOP(model, id) # better

def get_pdf_name(id):
    fac_obj = O.GiscedataFacturacioFactura
    f = fac_obj.browse(id)

    file_name = "{}_{}_Ê{}_GkWh{}_LANG{}_T{}".format(
        f.number,
        f.name,
        "1" if f.polissa_id.soci.id == 38039 else "0",
        "1" if f.is_gkwh else "0",
        f.partner_id.lang,
        f.tarifa_acces_id.name)
    return file_name + ".pdf"

def save_file(name, data, type='wb'):
    with open(name,type) as f:
        f.write(data)

def generate_and_save_pdf(id,name):
    try:
        pdf_data = generate_inv_pdf(id)
        step("saving pdf to {}",name)
        save_file(name, pdf_data)
        success("done!")
    except Exception as e:
        warn(str(e))

def generate_pdfs(f_ids):
    for count,id in enumerate(f_ids):
        step("generating pdf {}/{} id:{}",count+1,len(f_ids),id)
        pdf_name = get_pdf_name(id)
        generate_and_save_pdf(id,pdf_name)

def generate_pdfs_cases(cases):
    for count,key in enumerate(cases.keys()):
        step("generating pdf {}/{} cases: {}",count+1,len(cases.keys()),key)
        ids = cases[key]['ids']
        for id in ids:
            step("id:{}",id)
            generate_and_save_pdf(id,"{}-{}.pdf".format(id,key))

if __name__ == '__main__' :
    generate_pdfs(ids)

# vim: et ts=4 sw=4