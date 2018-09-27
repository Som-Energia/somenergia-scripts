#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from sheetfetcher import SheetFetcher
import os
from yamlns import namespace as ns
import io
from consolemsg import step, error, warn, fail , success
import csv
import dbconfig
from dbutils import nsList, csvTable
import re
from ooop import OOOP

def get_id_polissa_potencia_dist_from_drive():

    fetcher = SheetFetcher(
        documentName = config.document['filename'],
        credentialFilename = 'actualizarpotencias.json',
        )

    load_potenciadist = (",".join('\t'.join(c for c in row)
                for row in fetcher.get_range(config.document['sheet'],
                config.document['potenciaIntervalCells']))).encode('utf-8').split(',')

    load_idpolissa =  (",".join('\t'.join(c for c in row)
                for row in fetcher.get_range(config.document['sheet'],
                config.document['idpolissaIntervalCells']))).encode('utf-8').split(',')

    load_datainici = (",".join('\t'.join(c for c in row)
                for row in fetcher.get_range(config.document['sheet'],
                config.document['datainiciIntervalCells']))).encode('utf-8').split(',')
    load_potenciaactiva = (",".join('\t'.join(c for c in row)
                for row in fetcher.get_range(config.document['sheet'],
                config.document['potenciaactivaIntervalCells']))).encode('utf-8').split(',')



    step("Saving data into {}", "dades_id_polissa_potencia_dist.csv")

    with open("dades_id_polissa_potencia_dist.csv", "w") as loaddades:
         writer = csv.writer(loaddades, delimiter = "\t")
         writer.writerows( zip(load_potenciadist, load_idpolissa, load_datainici, load_potenciaactiva ))
    return load_idpolissa

def update_dades_erp(data):

    O = OOOP(**dbconfig.ooop)
    for d in data:

        potencia = float(d[0])*0.001
        id_polissa = int(d[1])
        data_inici = d[2]
        potencia_activa = float(d[3])*0.001
        data_firma = O.GiscedataPolissa.read(id_polissa,
                        ['data_firma_contracte'])['data_firma_contracte']

        step("Actualizando el id polissa {} con la nueva potencia {}",
            id_polissa,
            potencia,
            )
        p = O.GiscedataPolissa.read(id_polissa)
        O.GiscedataPolissa.send_signal([id_polissa],'modcontractual')
        O.GiscedataPolissa.write(id_polissa,{'potencia':potencia})
        observaciones_value =   """
                                Data %s: Canvi potencia %s a potencia %s per
                                dades no coincidents entre dades distribuidora i ERP
                                """ %(data_inici, potencia_activa, potencia)

        step("Generando periodos para el id polissa {}", id_polissa)
        O.GiscedataPolissa.generar_periodes_potencia([id_polissa])
        step("Modificando polissa {}", p['name'])
        parameters = {'accio':'modificar','polissa_id':id_polissa,'observacions':observaciones_value,'data_inici':data_inici,'data_firma_contracte':data_firma}
        # en accio nou hay que tener en cuenta las fechas de data_inici y data_final del anterior registro
        # parameters = {'accio':'nou','polissa_id':id_polissa,'observacions':observaciones_value,'data_inici':'2019-01-22','data_firma_contracte':data_firma,'data_final':'2020-01-22'}
        wizard_id = O.GiscedataPolissaCrearContracte.create(parameters)
        O.GiscedataPolissaCrearContracte.action_crear_contracte([wizard_id], {})
        success("Polissa {} con potencia antigua {} actualizada con potencia distri {}", p['name'], potencia_activa, potencia)
        cont += 1
def get_dades_from_csv():

     with open('dades_id_polissa_potencia_dist.csv') as csv_file:
         data = []
         for row in csv_file:
            data_line = row.rstrip().split('\t')
            data.append(data_line)
         return data

def main():

    step("Get all potenciadist from {} drive", config.document['filename'])
    get_id_polissa_potencia_dist_from_drive()
    data = get_dades_from_csv()
    update_dades_erp(data)

if __name__ == '__main__':

    try:
        config = ns.load("configdoc.yaml")
    except:
        error("Check configdoc.yaml")
        raise

    main()
