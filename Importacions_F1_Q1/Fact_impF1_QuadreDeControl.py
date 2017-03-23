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

data_carrega = '2017-03-19'

# Tipologies d'error. Diccionari amb string per humans i string per ERP
tipificacio_errors = {
        "A. TOTAL":'',
        "B. Divergencies en lectures": 'Divergència',
        "C. Sense Factura de referencia": 'trobat la factura de referència amb número',
        "D. Data erronia modificacions contractuals": 'La tarifa (',
        "E. Bloquejos amb altres importacions": 'deadlock',
        "F. Temps d'importacio massa llarg": 'timeout',
        "G. No es pot facturar a traves de lectures": ": No s'ha pogut facturar a trav",
        "G. Inicial": ": inicial",
        "G. Data inicial Comptador erronea": 'Error introduint lectures en data inicial',
        "H. Data final Comptador erronea": 'Error introduint lectures en data fi',
        "I. Sense pòlissa vinculada": 'lissa vinculada al cups',
        "J. No es troba el CUPS indicat": 'trobat el CUPS',
        "K. No es troba l'empresa emisora": 'Empresa emisora no correspon',
        "L. No s'han trobat tots els periodes": 'identificar tots els períodes',
        "M. Problemes amb la reactiva": "reactiva per facturar",
        "N. Comptador diferent de la polissa": 'assignat el comptador',
        "O. No existeix cap modificacio contractual": 'Error no existeix cap modificaci',
        "P. Intent de dividir entre 0": "float division",
        "R. No such field": 'child',
        "\nS. F1 ja importat": "ja s'ha processat",
        "T. XML erroni": 'XML no es correspon al tipus F1',
        "U. Document invalid": 'Document invàlid',
    }


print "ERRORS DE IMPORTACIONS de F1"
for error,error_erp in sorted(tipificacio_errors.items()):
    vals_search_f1 = vals_search + [('info', 'like', error_erp)]
    erronis_ids = imp_obj.search(vals_search_f1)
    print " -->" + " %s: %d" % (error,len(erronis_ids),)

