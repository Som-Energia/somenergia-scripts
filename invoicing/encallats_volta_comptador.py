#!/urs/bin/env python2
# -*- coding: utf-8 -*-
from consolemsg import step, success
from yamlns import namespace as ns
from erppeek import Client
import configdb
import csv
from tqdm import tqdm

def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
        )
    return parser.parse_args(namespace=ns())

filename = parseArguments().output

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

lot_obj = O.GiscedataFacturacioLot
clot_obj = O.GiscedataFacturacioContracte_lot
F1_obj = O.GiscedataFacturacioImportacioLinia

filecsv = open(filename, 'w')
csv_writer = csv.writer(filecsv, delimiter=';')

def encallat_volta_comptador(cups_id, data):
    f1_tipusR_ids = F1_obj.search([('cups_id','=',cups_id),('type_factura','=','R')])
    for f1_id in f1_tipusR_ids:
        f1 = F1_obj.browse(f1_id)
        for lectures in f1.importacio_lectures_ids:
            if lectures.fecha_actual == data:
                return True
    return False

def main():
    id_lot_obert = lot_obj.search([('state','=','obert')])[0]
    success("Lot actualment en us id {}", id_lot_obert)
    
    clot_ids = clot_obj.search([('lot_id', '=', id_lot_obert), ('tarifaATR','like', '2.%'),('status', 'like', '%[V001]%')])
    success("Factures 2.X amb V001 al lot actual trobades: {}", len(clot_ids))

    clot_ids = clot_ids[:10]

    csv_writer.writerow(['Nom polissa', 'Data ultima lectura facturada'])
    for clot_id in tqdm(clot_ids):
        cl = clot_obj.browse(clot_id)
        if encallat_volta_comptador(cl.polissa_id.cups.id, cl.polissa_id.data_ultima_lectura):
            csv_writer.writerow([cl.polissa_id.name, cl.polissa_id.data_ultima_lectura])
            step("trobada polissa {} amb F1 tipus R amb data final coincident amb data lectura final {}", cl.polissa_id.name, cl.polissa_id.data_ultima_lectura)

if __name__ == '__main__':
    main()

# vim: et ts=4 sw=4
