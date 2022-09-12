#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import sys
import traceback
import configdb
from erppeek import Client
from yamlns import namespace as ns
from consolemsg import step, success, error, warn


step("Connectant a l'erp")
O = Client(**configdb.erppeek)
step("Connectat")


#Objectes
fact_obj = O.GiscedataFacturacioFactura
rprt_obj = O.GiscedataFacturacioFacturaReport


# Found known errors
known_errors = {
    """'cc_name': fact.partner_bank.iban[:-5]+"*****" if pol.tipo_pago.code != 'TRANSFERENCIA_CSB' else pol.payment_mode_id.bank_id.iban+_(" (Som Energia, SCCL)"),""": "La polissa de la factura no te compte bancari!",
    """excempcio = excempcio[excempcio.find("(")+1:excempcio.find(")")]""": "Revisa la posició fiscal, text de la excempcio dona problemes!!",
}


def search_invoice_by_ids(invoice_ids):
    ret_ids = []
    invoice_ids = [int(i) for i in invoice_ids.split(',')]
    for invoice_id in invoice_ids:
        step("Cerquem la factura...", invoice_id)
        fact_ids = fact_obj.search([('id', '=', invoice_id)])
        if len(fact_ids) == 0:
            warn("Cap factura trobada amb aquest id!!")
        if len(fact_ids) > 1:
            warn("Multiples factures trobades!! {}", fact_ids)
        ret_ids.append(fact_ids[0])
        step("Factura amb ID {} existeix", fact_ids[0])
    return ret_ids


def search_invoice_by_id(invoice_id):
    step("Cerquem la factura... {}", invoice_id)
    fact_ids = fact_obj.search([('id', '=', invoice_id)])
    if len(fact_ids) == 0:
        warn("Cap factura trobada amb aquest id!!!!")
        return None
    if len(fact_ids) > 1:
        warn("Multiples factures trobades!! {}", fact_ids)
        return None
    fact_id = fact_ids[0]
    step("Factura amb ID {} existeix", fact_id)
    return fact_id


def search_invoice_by_name(invoice_number):
    step("Cerquem la factura...{}", invoice_number)
    fact_ids = fact_obj.search([('number', '=', invoice_number)])
    if len(fact_ids) == 0:
        warn("Cap factura trobada amb aquest numero!!")
        return None
    if len(fact_ids) > 1:
        warn("Multiples factures trobades!! {}", fact_ids)
        return None
    fact_id = fact_ids[0]
    step("Factura amb ID {} trobada", fact_id)
    return fact_id


def load_invoice_data(fact_id):
    step("Carregant dades de la factura...")
    error = False
    data = ""
    data_yaml = rprt_obj.get_components_data_yaml([fact_id])
    try:
        data = ns.loads(data_yaml)
    except Exception as e:
        error = True
        step("Error localitzat ...")
        data_yaml = data_yaml.replace("\n", '\n')
    return error, data_yaml

def print_invoice_data(fact_id):
    f = fact_obj.browse(fact_id)
    warn("Codi factura .... {}", f.number)
    warn("Id factura ...... {}", fact_id)
    warn("Polissa ......... {}", f.polissa_id.name)


def search_known_errors(res, fact_id):
    errors = []
    for k in known_errors.keys():
        if k in res:
            errors.append(known_errors[k])
    if errors:
        success("S'ha trobat {} possible(s) error(s):", len(errors))
        for error in errors:
            success("POSSIBLE ERROR >> {}", error)
    else:
        warn("Error no reconegut, fes captura i obre incidència!!")
    step("Traça interna de l'error:")
    step(res)
    return errors


def main(invoice_name, invoice_id, invoice_ids):
    fact_ids = []
    if invoice_name:
        fact_ids.append(search_invoice_by_name(invoice_name))
    if invoice_id:
        fact_ids.append(search_invoice_by_id(invoice_id))
    if invoice_ids:
        fact_ids.extend(search_invoice_by_ids(invoice_ids))

    for fact_id in fact_ids:
        if fact_id:
            print_invoice_data(fact_id)
            error, res = load_invoice_data(fact_id)
            if error:
                errors = search_known_errors(res, fact_id)
            else:
                success("La factura en pdf no te problemes a nivell de dades!")
                step(res)

def only_one(a, b, c):
    n = 0
    if bool(a):
        n += 1
    if bool(b):
        n += 1
    if bool(c):
        n += 1
    return n == 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(
            description='Comprovador del generador de dades de factures en pdf'
    )

    parser.add_argument(
        '--invoice_name',
        dest='i_name',
        help="Nom de la factura"
    )

    parser.add_argument(
        '--invoice_id',
        type=int,
        dest='i_id',
        help="Id de la factura"
    )

    parser.add_argument(
        '--invoice_ids',
        dest='i_ids',
        help="llista d'Id de les factures"
    )

    args = parser.parse_args()

    if not only_one(args.i_name, args.i_id, args.i_ids):
        parser.print_help()
        sys.exit()

    try:
        main(args.i_name, args.i_id, args.i_ids)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4