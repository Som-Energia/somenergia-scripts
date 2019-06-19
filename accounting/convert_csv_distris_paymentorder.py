#!/usr/bin/env python
# -*- coding: utf-8 -*-
import StringIO
import csv
import sys
import pandas as pd

## SYNTAX
# script.py facturasF55091367_20190603.csv

#DISTRI CONSTANTS
DISTRI_UFD = '0703'

class CSVParser:
    def __init__(self, invoice_list):
        self.invoice_list = invoice_list
        pass

    def parseUFD(self):
        #['13/05/2019', 'J419005384193', 'ES0022000008756135NE1P', '23,09']
        i = 0
        dist_line = []
        while i<len(self.invoice_list)-1:
            if len(self.invoice_list[i]) == 4:
                dist_line.append([self.invoice_list[i][1],self.invoice_list[i][3]])
            i += 1
        return dist_line[1:]

    def parseERP(self):
        #"J419004903723";"57.91";"No trobada"
        i = 0
        dist_line = []
        while i<len(self.invoice_list)-1:
            if len(self.invoice_list[i]) == 3:
                dist_line.append([self.invoice_list[i][0],self.invoice_list[i][1]])
            i += 1
        return dist_line[1:]

    def parseEndesa(self, xl):
        #Fecha_Factura;Indentificar_Emisora;ComentariosFactua...
        df1 = xl.parse(xl.sheet_names[1])
        df_obj = df1.select_dtypes(['object'])
        df1[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        df1 = df1.iloc[:-2]
        df1.to_csv(path_or_buf='output.csv', sep=';', columns=['Codigo_Fiscal_de_Factura','Importe_Total_de_la_Factura'], header=False, index=False, decimal=',')

        return 0

    def getDistribuidora(self):
        if not self.invoice_list:
            return -1
        i = 0
        dist_line = []
        erp_line = False #Recàrrega output fitxer ERP
        while i<len(self.invoice_list)-1:
            dist_line = filter(lambda x: 'SOCIEDAD' in x, self.invoice_list[i])
            if dist_line:
                break
            erp_line = filter(lambda x: 'No trobada' in x, self.invoice_list[i])
            if erp_line:
                break
            i += 1

        if any(DISTRI_UFD in s for s in dist_line):
            return self.parseUFD()
        elif erp_line:
            return self.parseERP()
        else:
            return 0

    def parser(self):
       return self.getDistribuidora()

    def build_report(self, records):
        csv_doc=StringIO.StringIO()
        writer_report = csv.writer(csv_doc, delimiter=';')

        if not records:
            return False

        for row in records:
            writer_report.writerow(row)

        doc = csv_doc.getvalue()

        return doc



invoices_file =  sys.argv[1]
outputFile =  sys.argv[2]
invoice_list = []
if invoices_file.endswith('.xlsx'):
    xl = pd.ExcelFile(invoices_file)
    print "Excel creat"
    endesa_line = filter(lambda x: 'Facturacion' in x, [xl.sheet_names[1]])
    if endesa_line:
        m = CSVParser([])
        m.parseEndesa(xl)

else:
    with open(invoices_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            invoice_list.append(row)

    m = CSVParser(invoice_list)
    new_file = m.parser()
    output = m.build_report(new_file)
    if new_file and output:
        with open(outputFile,'w') as f:
            f.write(output)
            print "Fitxer correcte creat"
    else:
        print "El format del fitxer no coincideix amb el de cap distri"
