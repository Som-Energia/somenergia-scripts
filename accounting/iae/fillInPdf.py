#!/usr/bin/env python3 

import csv
from fdfgen import forge_fdf
import os
import sys
from yamlns import namespace as ns
from tempfile import NamedTemporaryFile

#sys.path.insert(0, os.getcwd())
filename_prefix_016 = "016"
filename_prefix_703 = "703"

csv_file_016 = "IAE_016.csv"
csv_file_703 = "IAE_703.csv"
pdf_file_016 = "016.pdf"
pdf_file_703 = "703.pdf"

tmp_file = "tmp_file.fdf"
output_folder = 'output/'


def process_csv(filename):
    headers = []
    data =  []
    with open(filename, encoding='utf8') as file:
        csv_data = list(csv.reader(file))
        headers = csv_data[0]
        return [
            ns(
                (field, value.strip())
                for field, value in zip(headers, row)
            )
            for row in csv_data[1:]
        ]

def form_fill(pdf_file, outputdir, filename_prefix, filename_sufix, fields):
    output_file = '{0}{1}-{2}.pdf'.format(outputdir, filename_prefix, filename_sufix)
    print("Creating {}".format(output_file))
    fdf = forge_fdf(
        pdf_form_url="",
        fdf_data_strings=fields,
        fdf_data_names=[],
        fields_hidden=[],
        fields_readonly=[],
        checkbox_checked_name="On"
    )
    with NamedTemporaryFile() as fdf_file:
        fdf_file.write(fdf)
        fdf_file.flush()
        cmd = 'pdftk "{0}" fill_form "{1}" output "{2}" dont_ask'.format(pdf_file, fdf_file.name, output_file)
        os.system(cmd)

def fillPdfFromCsv(csv, pdf, outputdir, prefix, keyfield, extra=ns()):
    os.makedirs(outputdir, exist_ok=True)
    data = process_csv(csv)
    for row in data:
        row.update(extra)
        form_fill(pdf, outputdir, prefix, row[keyfield], row)

print('Generating Forms:')
print('-----------------------')

fillPdfFromCsv(
    csv=csv_file_016,
    pdf=pdf_file_016,
    outputdir=output_folder,
    keyfield='MUNICIPIMUNICIPIO_4',
    prefix=filename_prefix_016,
    extra = {
        'FI DACTIVITAT': True,
        'SUBJECTE PASSIUSUJETO PASIVO': True,
        'Empresarial': True,
        'undefined': True,
        'EMPRESARIAL': True,
        },
    )
fillPdfFromCsv(
    csv=csv_file_703,
    pdf=pdf_file_703,
    outputdir=output_folder,
    keyfield='12 Municipio de la actividad o local indirecto',
    prefix=filename_prefix_703,
    )


# vim: set ts=4 sw=4 et
