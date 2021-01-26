#!/usr/bin/env python3 

import csv
from fdfgen import forge_fdf
import os
import sys

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
    with open(filename) as file:
        csv_data = list(csv.reader(file))
        headers = csv_data[0]
        return [
            [
                (field, value)
                for field, value in zip(headers, row)
            ]
            for row in csv_data[1:]
        ]

def form_fill(pdf_file, filename_prefix, filename_sufix, fields):
  output_file = '{0}{1}-{2}.pdf'.format(output_folder, filename_prefix, filename_sufix)
  print("creating {}".format(output_file))
  fdf = forge_fdf(
    pdf_form_url="",
    fdf_data_strings=fields,
    fdf_data_names=[],
    fields_hidden=[],
    fields_readonly=[],
    checkbox_checked_name="On"
  )
  fdf_file = open(tmp_file,"wb")
  fdf_file.write(fdf)
  fdf_file.close()
  cmd = 'pdftk "{0}" fill_form "{1}" output "{2}" dont_ask'.format(pdf_file, tmp_file, output_file)
  os.system(cmd)
  os.remove(tmp_file)

os.makedirs(output_folder, exist_ok=True)
data_016 = process_csv(csv_file_016)
data_703 = process_csv(csv_file_703)
print('Generating Forms:')
print('-----------------------')
for fields in data_016:
  fields.extend([
    ('FI DACTIVITAT', True),
    ('SUBJECTE PASSIUSUJETO PASIVO', True),
    ('Empresarial', True),
    ('undefined', True),
    ('EMPRESARIAL', True),
  ])
  form_fill(pdf_file_016, filename_prefix_016, fields[21][1].strip(), fields)
for fields in data_703:
  form_fill(pdf_file_703, filename_prefix_703, fields[23][1].strip(), fields)

