#!/usr/bin/env python3

import csv
import sys
from pathlib import Path
from yamlns import namespace as ns
from yamlns.dateutils import Date
from slugify import slugify

municipi=None

csvfile, outputdir = sys.argv[1:]

Path(outputdir).mkdir(exist_ok=True)

# This parser is quite adhoc to the structure of the curent csv file
# Something like this
"""
"Albocàsser"
"Any","Trimestre","Pagaments a distribuidora","Factures a clients"
2020.0,4.0,209.42,295.42

"","","","","Ingresos bruts","Tasa","Total"
"Total","",209.42,295.42,86.0,1.5,1.29



"Alcalà de Xivert"
"Any","Trimestre","Pagaments a distribuidora","Factures a clients"
...
"""

def euros(text):
    "formats an amount as euro currency with two decimals"
    from decimal import Decimal
    return format(Decimal(text).quantize(Decimal('1.00'))).replace(".",",")

def floatInt(number):
    return int(float(number))

nextTellsYear=False
with Path(csvfile).open() as infile:
    reader = csv.reader(infile, delimiter=',', quotechar='"')
    for row in reader:
        if len(row) == 1:
            municipi = row[0]
            continue
        if not row:
            continue

        if nextTellsYear:
            year = floatInt(row[0])
            trimester = floatInt(row[1])
            nextTellsYear=False
        if row[0] == "Any":
            nextTellsYear=True

        if row[0] != "Total":
            continue
        (
            _, # "Total"
            _, # Empty
            paid_to_distribution,
            invoiced_amount,
            gross_amount,
            _, # Tax percent
            tax_amount,
        ) = row
        ns(
            municipi=" ".join(municipi.split(',')[::-1]).strip(),
            paid_to_distribution=euros(paid_to_distribution),
            invoiced_amount=euros(invoiced_amount),
            gross_amount=euros(gross_amount),
            tax_amount=euros(tax_amount),
            period=f"{trimester}T {year}",
            date=Date.today(),
        ).dump(Path(outputdir)/(slugify(municipi)+".yaml"))


