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

    step("Saving data into {}", "dades_id_polissa_potencia_dist.csv")

    with open("dades_id_polissa_potencia_dist.csv", "w") as loaddades:
         writer = csv.writer(loaddades, delimiter = "\t")
         writer.writerows( zip(load_potenciadist, load_idpolissa ))
    return load_idpolissa

def update_dades_erp(data):

    O = OOOP(**dbconfig.ooop)
    
    #print "".join([str(d) for d in data if d[0]=='5500'])
    for d in data:
        potencia = float(d[0])*0.001
        id_polissa = int(d[1])
        step("Actualizando el id polissa {} con la nueva potencia {}",
            id_polissa,
            potencia,
            )
        p = O.GiscedataPolissa.read(id_polissa)
        O.GiscedataPolissa.write(id_polissa,{'potencia':potencia})
        step("Generando periodos para el id polissa {}", id_polissa)
        O.GiscedataPolissa.generar_periodes_potencia([id_polissa])
        step("Modificando polissa {}", p['name'])
        # TODO: Que se añade a los campos Observaciones, data_inici, data_firma_contracte?
        parameters = {'accio':'modificar','polissa_id':id_polissa,'observacions':'TEST','data_inici':'2018-08-28','data_firma_contracte':'2018-08-28'}
        wizard_id = O.GiscedataPolissaCrearContracte.create(parameters)
        O.GiscedataPolissaCrearContracte.action_crear_contracte([wizard_id], {})
        success("Polissa {} actualizada con potencia {}", p['name'], potencia)
        data.pop(0)
        #el break lo pongo para que se aplique a la primera polissa para pruebas
        break
    
    success("Polissas que de actualizar {}", data)

def get_dades_from_csv():
    
     with open('dades_id_polissa_potencia_dist.csv') as csv_file:
         #csv_reader = csv.reader(csv_file, delimiter='\t')
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
