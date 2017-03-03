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

def fix_metter_contract(pol_id):
    pol_obj = O.GiscedataPolissa
    comp_obj = O.GiscedataLecturesComptador

    pol_read = pol_obj.read(pol_id,
            ['name', 'comptadors'])
    if not(pol_read['comptadors']):
        print "No te comptadors"
        return False
    comp_id = pol_read['comptadors'][0]
    comp_obj.write(comp_id,
                   {'data_baixa':False,
                    'active':True})
    return True

def contract_from_lin(lin_id):
    pol_obj = O.GiscedataPolissa
    lin_obj = O.GiscedataFacturacioImportacioLinia

    lin_read = lin_obj.read(lin_id,['cups_id'])
    if not(lin_read['cups_id']):
        return False
    cups_id = lin_read['cups_id'][0]
    print lin_read['cups_id']
    pol_ids = pol_obj.search([('cups', '=', cups_id)],0, 0, False, {'active_test': False})
    if not(pol_ids):
        print "no hi ha contracte vinculat al cups del F1"
        return False
    return pol_ids[0]

def informacio_contracte(pol_id):
    pol_obj = O.GiscedataPolissa
    pol_read = pol_obj.read(pol_id,
                    ['name','cups'])
    print "\n--> Contracte: %s" % pol_read['name']
    print "--> CUPS: %s" % pol_read['cups'][1]


def arreglar_importacio(linia_id,pol_id):
    lin_obj = O.GiscedataFacturacioImportacioLinia
    info = lin_obj.read(linia_id, ['info'])['info']
    txt_data_final = "Error introduint lectures en data final."
    value_return = {'Si': False,
                    'txt':None}

    if txt_data_final in info:
        if not pol_id:
            print "No puc arreglar F1 perque no hi ha polissa vinculada"
            return value_return
        fix_metter_contract(pol_id)
        value_return['Si'] = True
        value_return['txt'] = txt_data_final
        return value_return

    value_return['Si']=True
    return value_return

# TODO def rollback_contract(pol_id, lin_id, context={}):


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
    pol_id = contract_from_lin(lin_id)
    informacio_contracte(pol_id)

    per_arreglar = arreglar_importacio(lin_id,pol_id)['Si']
    if not per_arreglar:
        print "No reimportem perque no hem pogut arreglar el problema"
        continue

    reimportacio = reimportar_ok(lin_id)
    if reimportacio['ok']:
        print "Factura importada correctament!"
        lin_factura_generada.append(lin_id)
        continue
    if reimportacio['mateix_missatge']:
        lin_mateix_missatge.append(lin_id)
    else:
        lin_diferent_missatge.append(lin_id)
    print "%d/%d"%(count,total)

output(total,lin_factura_generada,lin_mateix_missatge,lin_diferent_missatge)

