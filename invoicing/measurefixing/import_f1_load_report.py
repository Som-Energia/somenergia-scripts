#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from validacio_eines import lazyOOOP
from consolemsg import step, success
from yamlns import namespace as ns
from datetime import datetime
import StringIO
import csv

how_many = 5000
csv_filename = 'out.csv'

Op = lazyOOOP()
success("Connected")

i_obj = Op.GiscedataFacturacioImportacio
li_obj = Op.GiscedataFacturacioImportacioLinia
lil_obj = Op.GiscedataFacturacioImportacioLiniaLectures

all_dates = {}

step("Getting the ids")
i_ids = i_obj.search([], limit=how_many)
step("Reading the data")
i_datas = i_obj.read(i_ids, ['data_carrega', 'num_xml', 'name'])

success("Searching across {} imports:", len(i_ids))
for count, i_data in enumerate(i_datas):
    imp = ns(i_data)
    imp.day_carrega = imp.data_carrega[:10]
    success("{}/{} date {} zip file {}",
            count+1, len(i_datas), imp.day_carrega, imp.name)
    if imp.day_carrega not in all_dates:
        all_dates[imp.day_carrega] = ns({
                                            'importacions': [],
                                            'num_xml': 0,
                                            'min': None,
                                            'max': None,
                                            'elapsed': None,
                                            'elapsed_c': 0
                                        })

    day_import = all_dates[imp.day_carrega]
    day_import.importacions.append(imp)
    day_import.num_xml += imp.num_xml

    li_ids = li_obj.search([('importacio_id', '=', imp.id)])
    if li_ids:
        lil_ids = lil_obj.search([('linia_id', 'in', li_ids)])
        perm_data = lil_obj.perm_read(lil_ids)
        dates = sorted([l['create_date'] for l in perm_data])

        if dates:
            s = datetime.strptime(dates[0][:18], '%Y-%m-%d %H:%M:%S')
            e = datetime.strptime(dates[-1][:18], '%Y-%m-%d %H:%M:%S')
            el = e-s

            step("  imported xml {}  first {}  last {} elapsed {}",
                 day_import.num_xml, s, e, el)

            day_import.min = min(day_import.min, s) if day_import.min else s
            day_import.max = max(day_import.max, e) if day_import.max else e

            if imp.num_xml > 100 and el.total_seconds() > 10: # noise filter
                if day_import.elapsed:
                    day_import.elapsed += el
                else:
                    day_import.elapsed = el
                day_import.elapsed_c += imp.num_xml

success("Days found : {}", len(all_dates.keys()))
csv_doc = StringIO.StringIO()
writer_report = csv.writer(csv_doc, delimiter=';')
writer_report.writerow([
    'Dia',
    'totals importats',
    'primer importat',
    'hora primer',
    'ultim importat',
    'diferencia',
    'parcial importats',
    'parcial temps',
    'parcial ratio'])

for day in sorted(all_dates.keys()):
    day_import = all_dates[day]

    diff = None
    secs = None
    ratio = None
    min_hour = None
    if day_import.min and day_import.max:
        diff = day_import.max - day_import.min
    if day_import.elapsed:
        secs = int(day_import.elapsed.total_seconds())
    if secs and day_import.elapsed_c:
        ratio = day_import.elapsed_c/float(secs)
    if day_import.min:
        min_hour = day_import.min.strftime('%H:%M:%S')

    step("Day {}  total imported xml {:6}  first {}  last {}  elapsed {:10}  \
 work count {:6} work time {:6} s  work rate {:<14} xml/s",
         day, day_import.num_xml, day_import.min, day_import.max, diff,
         day_import.elapsed_c, secs, ratio)
    writer_report.writerow([
                            day,
                            day_import.num_xml,
                            day_import.min,
                            min_hour,
                            day_import.max,
                            diff,
                            day_import.elapsed_c,
                            secs,
                            ratio])

doc = csv_doc.getvalue()
with open(csv_filename, 'w') as f:
    f.write(doc)
