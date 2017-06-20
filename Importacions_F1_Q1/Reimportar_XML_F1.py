#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# To do: problemes ne mostrar missatges que em reotrna el ERP
# Per temes de enconding

from ooop import OOOP
import configdb
import time
from consolemsg import fail
import traceback

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

def output(total,lin_factura_generada,lin_mateix_missatge,
            lin_diferent_missatge,lin_no_fixed):
    print "\nNO importades: no s'ha arreglat l'error. %d" % len(lin_no_fixed)
    print "Importacions erronies inicials: %d" % total
    print "Reimportacions que han generat factura:  %d" % len(lin_factura_generada)
    print "Importacions encara erronies: %d" % (len(lin_diferent_missatge)+len(lin_mateix_missatge))
    print "  - Amb el mateix missatge: %d" % len(lin_mateix_missatge)
    print "  - Amb un missatge diferent: %d" % len(lin_diferent_missatge)

def printTiException(e,comment=''):
    print "Excepció controlada: "+str(e)
    if comment:
        print comment
    print "Bolcat de pila per IT ------------------------------"
    traceback.print_exc()
    print "Bolcat de pila per IT finalizat --------------------"

def reimportar_ok(linia_id):
    import time
    lin_obj = O.GiscedataFacturacioImportacioLinia

    info_inicial = lin_obj.read([linia_id],['info'])[0]['info']
    lin_obj.process_line(linia_id)
    # TODO treure a parametres de configuracio
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

def fix_mod(info,pol_id):
    mod_obj = O.GiscedataPolissaModcontractual
    pol_obj = O.GiscedataPolissa

    from datetime import datetime, timedelta

    # TODO millorar com extreure informacio
    data_info = info[-63:-53]

    mod_contractuals = pol_obj.read(pol_id,
                    ['modcontractuals_ids'])['modcontractuals_ids']
    if len(mod_contractuals) <= 1:
        print "La polissa no te cap modificacio contractual"
        return False

    mod_actual = mod_obj.get(mod_contractuals[0])
    dies_a_moure = 1
    data_inici_dt = datetime.strptime(mod_actual.data_inici, '%Y-%m-%d')
    #  La tarifa (2.0A) de la pólissa 49549 no és la mateixa que la del
    # F1 (2.0DHA) el dia 2017-02-24. Comprovi que la tarifa de la
    # pólissa és la correcte
    if data_info != mod_actual.data_inici:
        data_info_dt = datetime.strptime(data_info, '%Y-%m-%d')
        # He tret el += de dies a moure. Valorar que es millor
        dies_a_moure = (data_info_dt - data_inici_dt).days

    if abs(dies_a_moure) > 10:
        print "Masses dies a moure. Millor fer manualment"
        return False

    moure_dies_modificacio(dies_a_moure,mod_contractuals[0],mod_contractuals[1])
    return True

def contract_from_lin(lin_id):
    pol_obj = O.GiscedataPolissa
    lin_obj = O.GiscedataFacturacioImportacioLinia
    if not lin_id:
        print "\nlin_id invalid --> " +str(lin_id)
        return False
    try:
        lin_read = lin_obj.read(lin_id,['cups_id'])
    except Exception as e:
        print "\nError de cerca "+str(lin_id)+" -> "+str(e)
        return False

    if not lin_read:
        print "\nlin_id Eliminat per acció d'usuari extern al script --> "+str(lin_id)
        return False

    if not(lin_read['cups_id']):
        print "\nlin_id sense cups vàlid --> "+str(lin_id)
        return False

    cups_id = lin_read['cups_id'][0]
    pol_ids = pol_obj.search([('cups', '=', cups_id)],0, 0, False, {'active_test': False})
    if not(pol_ids):
        print "\nno hi ha contracte vinculat al cups del F1"
        return False
    return pol_ids[0]

def informacio_contracte(pol_id):
    pol_obj = O.GiscedataPolissa
    pol_read = pol_obj.read(pol_id,
                    ['name','cups'])
    print "\n--> Contracte: %s" % pol_read['name']
    print "--> CUPS: %s" % pol_read['cups'][1]


def arreglar_importacio(linia_id,pol_id):
    #TODO: cal returnar el txt?
    lin_obj = O.GiscedataFacturacioImportacioLinia
    info = lin_obj.read(linia_id, ['info'])['info']
    txt_data_final = "Error introduint lectures en data final."
    txt_mod = "La tarifa ("
    txt_deadblock = "deadblock"
    txt_timeout = "timeout"

    value_return = {'Si': False,
                    'txt':None}

    if txt_data_final in info:
        value_return['txt'] = txt_data_final
        if not pol_id:
            print "No puc arreglar F1 perque no hi ha polissa vinculada"
            return value_return
        if not(fix_metter_contract(pol_id)):
            return value_return
    if txt_mod in info:
        if not(fix_mod(info, pol_id)):
            value_return['txt'] = txt_mod
            return value_return
    if txt_deadblock in info or txt_timeout in info:
        value_return['Si'] = True

    value_return['Si']=True
    return value_return

# TODO def rollback_contract(pol_id, lin_id, context={}):

def moure_dies_modificacio(dies,mod_actual_id, mod_antiga_id):
    mod_obj = O.GiscedataPolissaModcontractual

    from datetime import datetime, timedelta
    for a in range(abs(dies)):
        if dies > 0: b=1
        else:        b=-1
        mod_actual = mod_obj.get(mod_actual_id)
        mod_antiga = mod_obj.get(mod_antiga_id)

        data_final_inicial = mod_antiga.data_final
        data_final = datetime.strptime(mod_antiga.data_final, '%Y-%m-%d')
        data_final = datetime.strftime(data_final + timedelta(b), '%Y-%m-%d')
        try:
            mod_antiga.write({'data_final': data_final})
        except Exception as e:
            printTiException(e,"Mod contractual ANTIGA modificant data_final per:"
                "\n -dies: "+str(dies)+
                "\n -id:"+str(mod_antiga_id)+
                "\n -data:"+str(data_final))

        data_inicial = mod_actual.data_inici
        data_inici = datetime.strptime(mod_actual.data_inici, '%Y-%m-%d')
        data_inici = datetime.strftime(data_inici + timedelta(b), '%Y-%m-%d')
        try:
            mod_actual.write({'data_inici': data_inici})
        except Exception as e:
            printTiException(e,"Mod contractual ACTUAL modificant data_final per:" 
                "\n -dies: "+str(dies)+
                "\n -id:"+str(mod_actual_id)+
                "\n -data:"+str(data_inici))


args=parseargs()
if not args.cups and not args.info and not args.date:
    fail("Introdueix un cups o el missatge d'error o una data")

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
lin_no_fixed = []

for lin_id in lin_ids:
    count+=1
    pol_id = contract_from_lin(lin_id)
    if not pol_id: continue
    informacio_contracte(pol_id)

    fixed = arreglar_importacio(lin_id,pol_id)['Si']
    if not fixed:
        print "No reimportem perque no hem pogut arreglar el problema"
        lin_no_fixed.append(lin_id)
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

output(total,lin_factura_generada,lin_mateix_missatge,lin_diferent_missatge,lin_no_fixed)
