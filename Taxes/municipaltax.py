# -*- coding: utf-8 -*-

import StringIO
import csv
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom

import configdb

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

## SYNTAX
# script.py cities.csv 2015-01-01 2015-04-01 csv|xml
# cities.csv obtained from "Gestió agrupada impost 1.5%"

class MunicipalTaxesInvoicingReport:
    def __init__(self, cursor, start_date, end_date, tax, aggregated):
        self.cursor = cursor
        self.start_date = start_date
        self.end_date = end_date
        self.tax = tax
        self.aggregated = aggregated

        pass

    def by_city(self, ids, file_type):

        sql = '''
            SELECT
              municipi.name AS name,
              municipi.ine AS ine,
              EXTRACT(YEAR FROM invoice.date_invoice) AS invoice_year,
              EXTRACT(QUARTER FROM invoice.date_invoice) AS invoice_quarter,
              COALESCE(SUM(invoice_line.price_subtotal::float*(
              CASE
                WHEN factura_line.tipus IN ('subtotal_xml') AND invoice.type='in_invoice'  THEN 1
                WHEN factura_line.tipus IN ('subtotal_xml') AND invoice.type='in_refund'   THEN -1
                ELSE 0
              END
              )),0.0) AS provider_amount,
              COALESCE(SUM(invoice_line.price_subtotal::float*(
              CASE
                WHEN factura_line.tipus IN ('energia','reactiva','potencia') AND invoice.type='out_invoice' THEN 1
                WHEN factura_line.tipus IN ('energia','reactiva','potencia') AND invoice.type='out_refund'  THEN -1
                ELSE 0
              END
              )),0.0) AS client_amount
              FROM giscedata_facturacio_factura_linia AS factura_line
              LEFT JOIN account_invoice_line AS invoice_line ON invoice_line.id = factura_line.invoice_line_id
              LEFT JOIN giscedata_facturacio_factura AS factura ON factura.id = factura_line.factura_id
              LEFT JOIN account_invoice AS invoice ON invoice.id = factura.invoice_id
              LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
              LEFT JOIN giscedata_cups_ps AS cups ON cups.id = polissa.cups
              LEFT JOIN res_municipi as municipi on municipi.id = cups.id_municipi
              WHERE municipi.ID IN ({0})
                AND ((invoice.date_invoice >= '{1}') AND (invoice.date_invoice < '{2}'))
                AND (((invoice.type LIKE 'out_%%')
                  AND ((invoice.state = 'open') OR (invoice.state = 'paid')))
                  OR (invoice.type LIKE 'in_%%'))
            GROUP BY 1,2,3,4
            ORDER BY 1,2,3,4
            '''.format(','.join(map(str, ids)), self.start_date, self.end_date)

        self.cursor.execute(sql, {'start_date': self.start_date,
                                  'end_date': self.end_date,
                                  'ids': ids})

        return self.build_report(self.cursor.fetchall(), file_type)

    def build_report(self, records, file_type):
        invoicing_by_name = {}
        invoicing_by_date = {}
        ines = {}
        for record in records:
            name = record[0]
            ine = record[1]
            year = record[2]
            quarter = record[3]
            invoicing_by_name.setdefault(name, {'total_provider_amount': 0, 'total_client_amount': 0, 'quarters': []})
            invoicing_by_name[name]['total_provider_amount'] += record[4]
            invoicing_by_name[name]['total_client_amount'] += record[5]
            invoicing_by_name[name]['quarters'].append({
                'year': record[2],
                'quarter': record[3],
                'provider_amount': record[4],
                'client_amount': record[5]
            })

            invoicing_by_date.setdefault(year, {})
            invoicing_by_date[year].setdefault(quarter, {'total_provider_amount': 0, 'total_client_amount': 0})
            invoicing_by_date[year][quarter]['total_provider_amount'] += record[4]
            invoicing_by_date[year][quarter]['total_client_amount'] += record[5]
            ines.setdefault(name, ine)

        if file_type=='csv':
            ## CSV
            csv_doc=StringIO.StringIO()
            writer_report = csv.writer(csv_doc)

            for name,v in sorted(invoicing_by_name.items()):
                writer_report.writerow([name])
                writer_report.writerow(['Año', 'Trimestre', 'Pagos a distribuidora', 'Facturas a clientes'])
                for quarter in v['quarters']:
                    writer_report.writerow([
                        quarter['year'],
                        quarter['quarter'],
                        round(quarter['provider_amount'], 2),
                        round(quarter['client_amount'], 2)
                    ])

                writer_report.writerow([])
                writer_report.writerow(['', '', '', '', 'Ingresos brutos', 'Tasa', 'Total'])
                diff = v['total_client_amount'] - v['total_provider_amount']
                writer_report.writerow(['Total',
                                        '',
                                        round(v['total_provider_amount'], 2),
                                        round(v['total_client_amount'], 2),
                                        round(diff, 2),
                                        self.tax,
                                        round(diff*(self.tax/100.0), 2)
                                        ])
                writer_report.writerow([])

            writer_report.writerow([])
            writer_report.writerow(['Año', 'Trimestre', 'Pagos a distribuidora', 'Factuas a clientes', 'Ingresos',
                                    'Tasta', 'Total'])
            for year, v in sorted(invoicing_by_date.items()):
                for quarter, v in sorted(invoicing_by_date[year].items()):
                    diff = v['total_client_amount'] - v['total_provider_amount']
                    writer_report.writerow([
                            year,
                            quarter,
                            round(v['total_provider_amount'], 2),
                            round(v['total_client_amount'], 2),
                            round(diff, 2),
                            self.tax,
                            round(diff*(self.tax/100.0), 2)
                            ])
            doc = csv_doc.getvalue()

        if file_type == 'xml':
            ## XML 
            _empresa = Element("EMPRESA")
            _datos = SubElement(_empresa, 'DATOS')
            _nombre = SubElement(_datos, 'NOMBRE')
            _nombre.text = "Som Energia SCCL"
            _nif = SubElement(_datos, 'NIF')
            _nif.text = "F55091367"

            _municipios = SubElement(_empresa, 'MUNICIPIOS')
            for name,v in sorted(invoicing_by_name.items()):
                for quarter in v['quarters']:
                    _municipio = SubElement(_municipios, 'MUNICIPIO')
                    _ine = SubElement(_municipio, 'INEMUNICIPIO')
                    _ine.text = ines[name]
                    _ejercicio = SubElement(_municipio, 'EJERCICIO')
                    _ejercicio.text = str(int(quarter['year']))
                    _periodo = SubElement(_municipio, 'PERIODO')
                    _periodo.text = str(int(quarter['quarter']))
                    _fechaalta = SubElement(_municipio, 'FECHAALTA')
                    _fechabaja = SubElement(_municipio, 'FECHABAJA')
                    _tiposumin = SubElement(_municipio, 'TIPOSUMIN')
                    _tiposumin.text = '2'
                    _descsum = SubElement(_municipio, 'DESCSUM')
                    _descsum.text = 'Electricidad'
                    _descperi = SubElement(_municipio, 'DESCPERI')
                    _facturacion = SubElement(_municipio, 'FACTURACION')
                    _facturacion.text = '%0.2f' % quarter['client_amount']
                    _derechosacceso = SubElement(_municipio, 'DERECHOSACCESO')
                    _derechosacceso.text = '%0.2f' % quarter['provider_amount']
                    _compensacion = SubElement(_municipio, 'COMPENSACION')
                    _compensacion.text = '0.00'
                    _baseimponible = SubElement(_municipio, 'BASEIMPONIBLE')
                    diff = (quarter['client_amount'] - quarter['provider_amount'])
                    _baseimponible.text = '%0.2f' % diff
                    _cuotabasica = SubElement(_municipio, 'CUOTABASICA')
                    _cuotabasica.text = '%0.2f' % (self.tax/100)
                    _totalingresar = SubElement(_municipio, 'TOTALINGRESAR')
                    _totalingresar.text = '%0.2f' % (diff*(self.tax/100.0))
            doc = prettify(_empresa)

        return doc

import psycopg2
import psycopg2.extras
import csv
import sys

municipis_file =  sys.argv[1]
start_date =  sys.argv[2]
end_date =  sys.argv[3]
type_file =  sys.argv[4]


municipis_id = []
with open(municipis_file, 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        municipis_id.append(int(row[0]))

try:
    dbconn=psycopg2.connect(**configdb.psycopg)
except Exception, ex:
    print "Unable to connect to database " + configdb['DB_NAME']
    raise ex

m = MunicipalTaxesInvoicingReport(dbconn.cursor(), start_date,end_date,1.5,False)
print m.by_city(municipis_id, type_file)
