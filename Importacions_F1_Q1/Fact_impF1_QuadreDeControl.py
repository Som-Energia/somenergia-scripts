# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from consolemsg import fail

O = OOOP(**configdb.ooop)

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Reimportar els F1')
    parser.add_argument('-d', '--date',
        help="Escull data des de que comencem a fer la cerca",
        )
    return parser.parse_args()

args=parseargs()
if not args.date:
    fail("Introdueix una data de descarrega")

vals_search = [('state','=','erroni')]

if args.date:
    data_carrega = args.date
    def valid_date(date_text):
        from datetime import datetime
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return True
    data_carrega = data_carrega if data_carrega and valid_date(data_carrega) else None
    if data_carrega:
        vals_search += [('data_carrega','>=',data_carrega)]

imp_obj = O.GiscedataFacturacioImportacioLinia
et_obj = O.GiscedataFacturacioSwitchingErrorTemplate

et_ids = et_obj.search([])
templates_errors_read = et_obj.read(et_ids,['code','description'])
list_errors = sorted([{int(a['code'])+int(a['phase'])*1000:a['description']} for a in et_obj.read(et_ids,['code','phase','description'])])

print "ERRORS DE IMPORTACIONS de F1"
for a in list_errors:
    vals_search_f1 = vals_search + [('info', 'like', a.keys())]
    erronis_ids = imp_obj.search(vals_search_f1)
    if not erronis_ids:
        continue
    for b,c in a.items():
        print "  [" + str(b) + "]. Errors: ",str(len(erronis_ids))
        print u"  Descripció error: ", c , "\n"

