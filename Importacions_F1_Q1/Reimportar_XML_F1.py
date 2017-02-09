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
    return parser.parse_args()

def output(total, erronis_finals):
    print "Importacions erronies inicials: %d" % total
    print "Importacions correctes:  %d" % (total-erronis_finals)
    print "Importacions encara erronies: %d" % erronis_finals

def reimportar_ok(linia_id):
    info_inicial = lin_obj.read([linia_id],['info'])[0]['info']
    lin_obj.process_line(linia_id)
    time.sleep(15)
    info_nova = lin_obj.read([linia_id],['info'])[0]['info']
    if info_inicial == info_nova:
        #print "informacio igual: %s" % info_inicial
        print "Mateix missatge"
        return False
    #print "Missatge Inicial: %s \n Missatge Final: %s" % (info_inicial,info_nova)
    print "S'ha actualitzat el missatge"
    return True

args=parseargs()
if not args.cups and not args.info:
    fail("Introdueix un cups o el missatge d'error")

vals_search = [
    ('state','=','erroni'),
    ] + (
    [('cups_id.name','=',args.cups) ] if args.cups else []
    ) + (
    [('info','like',args.info) ] if args.info else []
    )

erronis_ids = lin_obj.search(vals_search)

#comptadors
count=0
total=len(erronis_ids)

print "Hi ha %d amb importacions erronies inicials" % total

#Incialitzem comptadors
imp_sense_canvis = []
imp_amb_canvi = []

for linia_id in erronis_ids:
    count+=1
    if reimportar_ok(linia_id):
        imp_sense_canvis.append(linia_id)
    else:
        imp_amb_canvi.append(linia_id)
    print "%d/%d"%(count,total)
erronis_finals_ids = lin_obj.search(vals_search)  
erronis_finals = len(erronis_finals_ids)

output(total,erronis_finals)

