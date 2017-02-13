#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# To do: problemes ne mostrar missatges que em reotrna el ERP
# Per temes de enconding

from ooop import OOOP
import configdb
import time
from consolemsg import fail

O = OOOP(**configdb.ooop)

lin_obj = O.GiscedataFacturacioImportacioLinia

def parseargs():
    import argparse
    parser = argparse.ArgumentParser(description='Reimportar els F1')
    parser.add_argument('-c', '--cups',
        help="Escull per cups",
        )
    parser.add_argument('-i', '--info',
        help="Escull F1 per missatge d'error",
        )
    parser.add_argument('-d', '--date',
        help="Escull data des de que comencem a fer la cerca",
        )
    return parser.parse_args()

def output(total,lin_factura_generada,lin_mateix_missatge,lin_diferent_missatge):
    print "Importacions erronies inicials: %d" % total
    print "Reimportacions que han generat factura:  %d" % len(lin_factura_generada)
    print "Importacions encara erronies: %d" % (len(lin_diferent_missatge)+len(lin_mateix_missatge))
    print "  - Amb el mateix missatge: %d" % len(lin_mateix_missatge)
    print "  - Amb un missatge diferent: %d" % len(lin_diferent_missatge)

def reimportar_ok(linia_id):
    import time
    lin_obj = O.GiscedataFacturacioImportacioLinia
    info_inicial = lin_obj.read([linia_id],['info'])[0]['info']
    lin_obj.process_line(linia_id)
    time.sleep(15)
    lin_read = lin_obj.read([linia_id],['info','conte_factures'])
    info_nova = lin_read[0]['info']
    conte_factures = lin_read[0]['conte_factures']
    value = {'mateix_missatge':False,'ok':False}
    if lin_read[0]['conte_factures']:
        value['ok'] = True
    if info_inicial == info_nova:
        #print "informacio igual: %s" % info_inicial
        print "Mateix missatge"
        value['mateix_missatge']=True
    else:
        #print "Missatge Inicial: %s \n Missatge Final: %s" % (info_inicial,info_nova)
        print "S'ha actualitzat el missatge"
    return value

args=parseargs()
if not args.cups and not args.info and not args.date:
    fail("Introdueix un cups o el missatge d'error")

vals_search = [
    ('state','=','erroni'),
    ] + (
    [('cups_id.name','=',args.cups) ] if args.cups else []
    ) + (
    [('info','like',args.info) ] if args.info else []
    )

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

lin_ids = lin_obj.search(vals_search)

#comptadors
count=0
total=len(lin_ids)

print "Hi ha %d amb importacions erronies inicials" % total

#Incialitzem comptadors
lin_factura_generada = []
lin_mateix_missatge = []
lin_diferent_missatge = []

for lin_id in lin_ids:
    count+=1
    reimportacio = reimportar_ok(lin_id)
    if reimportacio['ok']:
        print "Factura importada correctament!"
        lin_factura_generada.append(lin_id)
        break
    if reimportacio['mateix_missatge']:
        lin_mateix_missatge.append(lin_id)
    else:
        lin_diferent_missatge.append(lin_id)
    print "%d/%d"%(count,total)

output(total,lin_factura_generada,lin_mateix_missatge,lin_diferent_missatge)

