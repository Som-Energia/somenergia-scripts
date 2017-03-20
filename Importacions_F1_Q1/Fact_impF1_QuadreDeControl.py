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
        vals_search += [('data_carrega','>',data_carrega)]

imp_obj = O.GiscedataFacturacioImportacioLinia

data_carrega = '2017-03-19'

erronis_ids = imp_obj.search(vals_search)
erronis = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','Ja existeix una factura'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_ja = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','Divergència'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_div = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','La tarifa ('),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_tar = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','trobat la factura de referència amb número'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_ref = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','Error introduint lectures en data inicial'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_dat_in = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','Error introduint lectures en data fi'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_dat_fi = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','identificar tots els períodes'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_per = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','trobat el CUPS'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_cups = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','assignat el comptador'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_comp = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','lissa vinculada al cups'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_pol_cups = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','Empresa emisora no correspon'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_emp = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','Error no existeix cap modificació'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_mod = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','float division'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_float = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','XML erroni'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_xml = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','Document invàlid'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_invalid = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like','child'),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_child = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like',"No s'ha pogut identificar tots els períodes de reactiva per facturar"),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_reactiva = len(erronis_ids)

vals_search = [('state','=','erroni'),('info','like',"XML no es correspon al tipus F1"),('data_carrega','>',data_carrega)]
erronis_ids = imp_obj.search(vals_search)
err_no_F1 = len(erronis_ids)


print "ERRORS DE IMPORTACIONS"
print "TOTAL: %d" % erronis
print " --> Divergències: %d" % err_div
print " --> Factura de Referència: %d" % err_ref
print " --> Data Inicial Erronia: %d" % err_dat_in
print " --> Data final Erronia: %d" % err_dat_fi
print " --> Tarifa errònia: %d" % err_tar
print " --> Error Periodes: %d" % err_per
print " --> Sense CUPS : %d" % err_cups 
print " --> Comptador diferent de la pòlissa: %d" % err_comp
print " --> No hi ha cap polissa vincula al cups: %d" % err_pol_cups 
print " --> Empresa emisora no correspon: %d" % err_emp
print " --> No existeix cap modificació contractual: %d" % err_mod
print " --> Float division by zero: %d" % err_float
print " --> XML_erroni: %d" % err_xml
print " --> Document invàlid: %d" % err_invalid
print " --> No such child: %d" % err_child
print " --> Problemes amb la reactiva: %d" % err_child
print "--> Ja existeix una factura..: %d" % err_ja
print "--> XML no es correspon al tipus F1: %d" % err_no_F1

desajust = erronis - err_no_F1 - err_per - err_dat_fi - err_dat_in - err_ref - err_tar - err_div -err_comp - err_pol_cups -err_emp -err_reactiva - err_mod - err_float - err_xml -err_invalid -err_cups - err_child -err_ja

print "\n SENSE IDENTIFICAR --> %d" % desajust
