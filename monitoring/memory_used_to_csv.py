#!/urs/bin/env python2
# -*- coding: utf-8 -*-

"""
This script gets the given file (result of a top command with a predermined structure) and 
converts the information to a csv.
OUTPUT:
1. ["DATE", "HOUR", "PID", "PPID", "USER", "PR", "NI", "VIRT", "RES", "SHR", "S", "%CPU", "%MEM", "TIME+", "COMMAND"]
2. ["DATE", "COMMAND", "INST", "MEM"] on DATE i date + hour
"""

import csv
import datetime
from yamlns import namespace as ns
from memory_erp import selector

months = {
    'Jan':1,
    'Feb':2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12,
    }


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
csv_writer.writerow(["DATE", "COMMAND", "INST", "MEM"])
data_date = False
data_row = []


acc = {}
for row in rows:
    if row == []:
        continue
    if '##################' in row[0]:
        for command in sorted(acc.keys()):
            csv_writer.writerow([date_hour, command, comma(str(acc[command]['inst'])), comma(str(acc[command]['mem']))])
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
        last_data_row = selector(last_data_row)

        if last_data_row not in acc:
            acc[last_data_row] = {'mem':0.0 ,'inst':0}

        data = acc[last_data_row]
        acc[last_data_row] = {
            'mem': data['mem'] + float(data_row[10]),
            'inst': data['inst'] + 1,
            }
