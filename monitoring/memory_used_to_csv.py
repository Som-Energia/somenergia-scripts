#!/urs/bin/env python2
# -*- coding: utf-8 -*-

"""
This script gets the given file (result of a top command with a predermined structure) and 
converts the information to a csv.
"""

import csv
from yamlns import namespace as ns
import datetime

months = {'Jan':1,'Feb':2}

def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'input',
        type=str,
        help="Input log file",
        )
    parser.add_argument(
        'output',
        type=str,
        help="Output csv file",
        )
    parser.add_argument(
        'output2',
        type=str,
        help="Output csv file acc",
        )
    return parser.parse_args(namespace=ns())

def comma(text):
    return text.replace('.',',')

args = parseArguments()
input_file = args.input
output_file = args.output
output_file2 = args.output2

rows = []
with open(input_file, 'r') as filelog:
    log_reader = csv.reader(filelog, delimiter='\n')
    for row in log_reader:
        rows.append(row)

filecsv = open(output_file, 'w')
csv_writer = csv.writer(filecsv, delimiter=';')
csv_writer.writerow(["DATE", "HOUR", "PID", "PPID", "USER", "PR", "NI", "VIRT", "RES", "SHR", "S", "%CPU", "%MEM", "TIME+", "COMMAND"])
data_date = False
data_row = []
for row in rows:
    if row == [] or '##################' in row[0]:
        continue
    if 'CET 202' in row[0]:
        date = row[0][4:10]

        month = months[row[0][4:7]]
        day = int(row[0][8:10])
        year = int(row[0][-4:])
        date = datetime.date(year,month,day).strftime("%Y/%m/%d")

        hour = row[0][11:16]
        data_date = False
        continue
    if 'PID' in row[0]:
        data_date = True
        continue
    if data_date:
        data_row = row[0].split()
        last_data_row = ' '.join(data_row[12:])
        csv_writer.writerow([date, hour, data_row[0], data_row[1], data_row[2], data_row[3],
                            data_row[4], data_row[5], data_row[6], data_row[7],
                            data_row[8], comma(data_row[9]), comma(data_row[10]), data_row[11], last_data_row])

filecsv = open(output_file2, 'w')
csv_writer = csv.writer(filecsv, delimiter=';')
csv_writer.writerow(["DATE", "COMMAND", "MEM"])
data_date = False
data_row = []


grouped_commands = [
    'wkhtmltopdf',
    'tmux',
    'git',
    'pdftk',
    'multitail',
    'crontab_actions'
]

def grouped(command):
    for gr in grouped_commands:
        if gr in command:
            return gr
    return command

acc = {}
for row in rows:
    if row == []:
        continue
    if '##################' in row[0]:
        for command in sorted(acc.keys()):
            csv_writer.writerow([date_hour, command, comma(str(acc[command]))])
        acc = {}
        continue

    if 'CET 202' in row[0]:
        date = row[0][4:10]

        month = months[row[0][4:7]]
        day = int(row[0][8:10])
        year = int(row[0][-4:])
        date = datetime.date(year,month,day).strftime("%Y/%m/%d")

        hour = row[0][11:16]
        date_hour = date+" "+hour
        data_date = False
        continue
    if 'PID' in row[0]:
        data_date = True
        acc = {}
        continue
    if data_date:
        data_row = row[0].split()
        last_data_row = ' '.join(data_row[12:])
        last_data_row = grouped(last_data_row)
        if last_data_row in acc:
            acc[last_data_row] = acc[last_data_row] + float(data_row[10])
        else:
            acc[last_data_row] = float(data_row[10])
