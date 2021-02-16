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
    """'cc_name': fact.partner_bank.iban[:-5]+"*****" if pol.tipo_pago.code != 'TRANSFERENCIA_CSB' else pol.payment_mode_id.bank_id.iban+_(" (Som Energia, SCCL)"),""": "La polissa de la factura no te compte bancari!"
}


def search_invoice(invoice_number):
    step("Cerquem la factura...")
    fact_ids = fact_obj.search([('number','=',invoice_number)])
    if len(fact_ids) == 0:
        warn("Cap factura trobada!!")
        return None
    if len(fact_ids) > 1:
        warn("Multiples factures trobades!! {}",fact_ids)
        return None
    fact_id = fact_ids[0]
    step("Factura amb ID {} trobada",fact_id)
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
        data = data_yaml.replace("\n",'\n')
    return error, data


def search_known_errors(res, fact_id):
    errors = []
    for k in known_errors.keys():
        if k in res:
            errors.append(known_errors[k])
    if errors:
        success("S'ha trobat {} possible(s) error(s):",len(errors))
        for error in errors:
            success(error)
    else:
        f = fact_obj.browse(fact_id)
        warn("Error no reconegut, fes captura i obre incidència!!")
        warn("Codi factura .... {}", f.number)
        warn("Id factura ...... {}", fact_id)
        warn("Polissa ......... {}", f.polissa_id.name)

    step("Traça interna de l'error:")
    step(res)
    return errors


def main(fact_name):
    fact_id = search_invoice(fact_name)
    if fact_id:
        error, res = load_invoice_data(fact_id)
        if error:
            errors = search_known_errors(res, fact_id)
        else:
            success("La factura en pdf no te problemes a nivell de dades!")


if __name__=='__main__':
    parser = argparse.ArgumentParser(
            description=''
    )

    parser.add_argument(
        '--invoice_name',
        dest='inv_name',
        required=True,
        help="Nombre de la factura"
    )

    args = parser.parse_args()

    try:
        main(args.inv_name)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4