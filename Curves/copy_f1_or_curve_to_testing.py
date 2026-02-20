#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import sys
import traceback
import configdb
from erppeek import Client
from yamlns import namespace as ns
from consolemsg import step, success, error, warn
from tqdm import tqdm


def search_invoices_by_names(c, invoice_names):
    return c.GiscedataFacturacioFactura.search([
        ('number', 'in', invoice_names.split(',')),
        ('type', 'in', ['out_invoice', 'out_refund']),
    ])


def search_invoices_by_ids(c, invoice_ids):
    return c.GiscedataFacturacioFactura.search([
        ('id', 'in', invoice_ids.split(',')),
        ('type', 'in', ['out_invoice', 'out_refund']),
    ])


def search_invoices_by_polissa_names(c, polissa_names):
    return c.GiscedataFacturacioFactura.search([
        ('polissa_id.name', 'in', polissa_names.split(',')),
        ('type', 'in', ['out_invoice', 'out_refund']),
    ])


def search_invoices_by_polissa_ids(c, polissa_ids):
    return c.GiscedataFacturacioFactura.search([
        ('polissa_id', 'in', polissa_ids.split(',')),
        ('type', 'in', ['out_invoice', 'out_refund']),
    ])


def search_f1_by_ids(c, f1_ids):
    return c.GiscedataFacturacioImportacioLinia.search([
        ('id', 'in', f1_ids.split(',')),
    ])


def search_f1_by_numero_factura_origen(c, origen_names):
    return c.GiscedataFacturacioImportacioLinia.search([
        ('invoice_number_text', 'in', origen_names.split(',')),
    ])


def download_curve_file_from_prod(fact_id):
    PRO = Client(**configdb.erppeek_profiles.prod)

    att_obj_prod = PRO.IrAttachment
    att_ids = att_obj_prod.search([
        ('res_model','=','giscedata.facturacio.factura'),
        ('res_id','=',fact_id),
        ('name','like','CURVE_%.csv')
    ])

    if not att_ids:
        warn("No s'ha trobat cap fitxer de corba per la factura a PROD {}", fact_id)
        return False
    if len(att_ids) > 1:
        warn("S'han trobat més d'un fitxer de corba per la factura a PROD {}", fact_id)    
        return False

    att_data = att_obj_prod.read(att_ids[0], ['datas', 'name'])
    with open('curve_file.csv', 'wb') as f:
        f.write(att_data['datas'].decode('base64'))
    step("S'ha descarregat el fitxer de corba de PROD per la factura {}: {}", fact_id, att_data['name'])
    return att_data['name']


def delete_curve_file_from_test_server(c, server, fact_id, file_name):
    att_ids = c.IrAttachment.search([
        ('res_model','=','giscedata.facturacio.factura'),
        ('res_id','=',fact_id),
        ('name','=',file_name)
    ])

    if not att_ids:
        warn("No s'ha trobat cap fitxer de corba per la factura a {} {}", server, fact_id)
        return False
    if len(att_ids) > 1:
        warn("S'han trobat més d'un fitxer de corba per la factura a {} {}", server, fact_id)    
        return False

    c.IrAttachment.unlink(att_ids)
    step("S'ha eliminat el fitxer de corba de {} per la factura {}: {}", server, fact_id, file_name)
    return True


def attach_curve_prod_file_to_test_server(c, server, fact_id, file_name):
    with open('curve_file.csv', 'rb') as f:
        data = f.read().encode('base64')

    c.IrAttachment.create({
        'name': file_name,
        'datas_fname': file_name,
        'res_model': 'giscedata.facturacio.factura',
        'res_id': fact_id,
        'datas': data,
    })
    step("S'ha adjuntat el fitxer de corba de PROD a {} per la factura {}: {}", server, fact_id, file_name)
    return True


def download_attached_f1_file_from_prod(f1_id):
    PRO = Client(**configdb.erppeek_profiles.prod)

    att_obj_prod = PRO.IrAttachment
    att_ids = att_obj_prod.search([
        ('res_model','=','giscedata.facturacio.importacio.linia'),
        ('res_id','=',f1_id),
        ('name','like','%.csv')
    ])

    if not att_ids:
        warn("No s'ha trobat cap fitxer adjunt per l'F1 a PROD {}", f1_id)
        return False
    if len(att_ids) > 1:
        warn("S'han trobat més d'un fitxer adjunt per l'F1 a PROD {}", f1_id)    
        return False

    att_data = att_obj_prod.read(att_ids[0], ['datas', 'name'])
    with open('f1_file.xml', 'wb') as f:
        f.write(att_data['datas'].decode('base64'))
    step("S'ha descarregat el fitxer adjunt de PROD per l'F1 {}: {}", f1_id, att_data['name'])
    return att_data['name']


def delete_attached_f1_file_from_test_server(c, server, f1_id, file_name):
    att_ids = c.IrAttachment.search([
        ('res_model','=','giscedata.facturacio.importacio.linia'),
        ('res_id','=',f1_id),
        ('name','=',file_name)
    ])

    if not att_ids:
        warn("No s'ha trobat cap fitxer adjunt per l'F1 a {} {}", server, f1_id)
        return False
    if len(att_ids) > 1:
        warn("S'han trobat més d'un fitxer adjunt per l'F1 a {} {}", server, f1_id)    
        return False

    c.IrAttachment.unlink(att_ids)
    step("S'ha eliminat el fitxer adjunt de {} per l'F1 {}: {}", server, f1_id, file_name)
    return True


def attach_attached_f1_file_to_test_server(c, server, f1_id, file_name):
    with open('f1_file.xml', 'rb') as f:
        data = f.read().encode('base64')

    c.IrAttachment.create({
        'name': file_name,
        'datas_fname': file_name,
        'res_model': 'giscedata.facturacio.importacio.linia',
        'res_id': f1_id,
        'datas': data,
    })
    step("S'ha adjuntat el fitxer adjunt de PROD a {} per l'F1 {}: {}", server, f1_id, file_name)
    return True


def main(invoice_names, invoice_ids, polissa_names, polissa_ids, f1tx_ids, origen_names, server, doit):

    if doit:
        success("Es FARAN CANVIS!")
    else:
        success("NO es faran canvis!")

    step("Connectant a l'erp {}", server)
    c = Client(**configdb.erppeek_profiles[server])
    step("Connectat")

    fact_ids = []
    if invoice_names:
        fact_ids.extend(search_invoices_by_names(c, invoice_names))
    if invoice_ids:
        fact_ids.extend(search_invoices_by_ids(c, invoice_ids))
    if polissa_names:
        fact_ids.extend(search_invoices_by_polissa_names(c, polissa_names))
    if polissa_ids:
        fact_ids.extend(search_invoices_by_polissa_ids(c, polissa_ids))

    success("S'han trobat {} factures", len(fact_ids))

    f1_ids = []
    if f1_ids:
        f1_ids.extend(search_f1_by_ids(c, f1tx_ids))
    if f1_ids:
        f1_ids.extend(search_f1_by_numero_factura_origen(c, origen_names))

    success("S'han trobat {} F1s", len(f1_ids))

    for fact_id in tqdm(fact_ids):
        if fact_id:
            file_name = download_curve_file_from_prod(fact_id)
            if doit and file_name:
                if delete_curve_file_from_test_server(c, server, fact_id, file_name):
                    attach_curve_prod_file_to_test_server(c, server, fact_id, file_name)

    for f1_id in tqdm(f1_ids):
        if f1_id:
            file_name = download_attached_f1_file_from_prod(f1_id)
            if doit and file_name:
                if delete_attached_f1_file_from_test_server(c, server, f1_id, file_name):
                    attach_attached_f1_file_to_test_server(c, server, f1_id, file_name)

    success("S'han trobat {} factures", len(fact_ids))


def only_one(items):
    n = 0
    for item in items:
        if bool(item):
            n += 1
    return n == 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(
            description='Script DESTRUCTIU per substituir els fitxers de corbes de les factures per les que hi ha a les polisses'
    )

    parser.add_argument(
        '--invoice_names',
        dest='i_names',
        help="Noms de la factures"
    )

    parser.add_argument(
        '--invoice_ids',
        dest='i_ids',
        help="llista d'Id de les factures"
    )

    parser.add_argument(
        '--polissa_names',
        dest='p_names',
        help="Noms de les polisses"
    )

    parser.add_argument(
        '--polissa_ids',
        dest='p_ids',
        help="llista d'Id de les polisses"
    )

    parser.add_argument(
        '--f1_ids',
        dest='f1_ids',
        help="llista d'Id dels F1"
    )

    parser.add_argument(
        '--origen_names',
        dest='origen_names',
        help="llista de Numeros Factura Origen dels F1"
    )

    parser.add_argument(
        '--doit',
        dest='doit',
        help="Realitzar els canvis"
    )

    parser.add_argument(
        '--server',
        help="Servidor destí",
        choices=[
            x
            for x in configdb.ooop_profiles.keys()
            if x != 'prod'
        ]
    )

    args = parser.parse_args()

    if not only_one([args.i_names, args.i_ids, args.p_names, args.p_ids]):
        parser.print_help()
        sys.exit()

    try:
        main(
            args.i_names,
            args.i_ids,
            args.p_names,
            args.p_ids,
            args.f1_ids,
            args.origen_ids,
            args.server,
            args.doit == 'do'
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4