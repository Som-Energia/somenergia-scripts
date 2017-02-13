#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb
from datetime import datetime,timedelta

from validacio_eines import *
from fix_invoice import *
from utils import *

O = OOOP(**configdb.ooop)

pol_obj = O.GiscedataPolissa
clot_obj = O.GiscedataFacturacioContracte_lot
comp_obj = O.GiscedataLecturesComptador
lect_fact_obj = O.GiscedataLecturesLectura
lect_pool_obj = O.GiscedataLecturesLecturaPool
fact_obj = O.GiscedataFacturacioFactura
cups_obj = O.GiscedataCupsPs
partner_obj = O.ResPartner

contracts_max = 100
invoices_max = 3

dif_maxima = 55
euro_max = 1000
euro_perday_max = euro_max/31
kwh_max = 9000
kwh_perday_max = kwh_max/31

def get_detained():
    lectures_massa_diferencia = []
    error_al_comptador_inactiu = []

    pol_ids = buscar_errors_lot_ids("La lectura actual és inferior a l'anterior")
    pol_ids = sorted(list(set(pol_ids)))

    #Comptadors visuals
    total = len(pol_ids)
    n = 0

    errors = []
    print pol_ids
    for pol_id in pol_ids:
        n += 1
        pol_read = pol_obj.read(pol_id,
            ['name',
             'comptador',
             'comptadors',
             'tarifa',
             'data_ultima_lectura',
             'distribuidora',
             'lot_facturacio',
             'cups',
             'category_id'])

        if pol_id == 45536:
            continue
        try:
            #Comprovar si s'està gestionant
            if es_cefaco(pol_id):
                continue
            #Comprovar comptadors i execpecions
            if not(pol_read['comptadors']):
                continue

            comp_id = pol_read['comptador']
            for comp_id in pol_read['comptadors']:
                comp_read = comp_obj.read(comp_id, ['giro','name'])
                #Comprovar si té gir de comptador
                if not(comp_read['giro']):
                    continue

                if not(comp_read['name'] == pol_read['comptador']):
                    continue
                #Cerca de lectures problematiques
                limit_superior_consum = int(comp_read['giro'])* 9/10
                lect_search_vals = [('comptador','=',comp_id),
                                    ('consum','>',limit_superior_consum),
                                    ('name','>=',pol_read['data_ultima_lectura'])]
                lect_ids = lect_fact_obj.search(lect_search_vals)
                if lect_ids:
                    #Ja tenim identificat el comptador i lectures amb problemes
                    break

            #Iterem per lectura problematica
            for lect_id in lect_ids:
                #Si el comptador no és l'actiu, s'ha d'anar amb cuidado perque pot ser que li facturem malament
                if not(comp_read['name'] == pol_read['comptador']):
                    break
                lectura = lect_fact_obj.get(lect_id)
                # Problemes amb lectures de Fenosa. Per ara només els filtrem
                # A sota hi ha codi de com solucionar-ho
                if lectura.lectura == 0 and pol_read['distribuidora'][0] == 2316:
                    break
                # Busquem la lectura de la data final de l'ultima factura
                search_vals_ref = [('comptador','=',lectura.comptador.name),
                                ('tipus','=',lectura.tipus),
                                ('periode','like', lectura.periode.name),
                                ('name','=', pol_read['data_ultima_lectura'])]
                lect_ref_id = lect_fact_obj.search(search_vals_ref)[0]
                lect_ref_read = lect_fact_obj.read(lect_ref_id,['lectura'])

                ##BUSCAR SI TE UNA LECTURA POSTERIOR
                search_vals_post = [('comptador','=',lectura.comptador.name),
                                ('tipus','=',lectura.tipus),
                                ('periode','like', lectura.periode.name),
                                ('name','>',lectura.name),
                                ('lectura','>=',lect_ref_read['lectura'])]
                lect_post_ids = lect_pool_obj.search(search_vals_post)

                if lect_post_ids:
                    break

                lect_search_vals_mult = [('comptador','=',comp_id),
                                    ('tipus','=',lectura.tipus),
                                    ('periode','like', lectura.periode.name),
                                    ('name','>',pol_read['data_ultima_lectura'])]

                lect_mult_ids = lect_fact_obj.search(lect_search_vals_mult)

                if len(lect_mult_ids) > 1:
                    # TODO: TO BE REVIEWD #
                    # Té lectures múltiples. Eliminem la penultima lectura entrada"
                    break

                if not(lect_ref_read['lectura']):
                    # No trobem lectura de referencia
                    break

                lectures_dif = lect_ref_read['lectura'] - lectura.lectura
                no_consum_mensual = False
                cups_id = pol_read['cups'][0]
                cups_read = cups_obj.read(cups_id,['conany_kwh'])
                if not(cups_read):
                    dif_maxima = 55.0
                    no_consum_mensual =  True
                else:
                    dif_maxima = cups_read['conany_kwh']/12.0

                if  0 < lectures_dif <= dif_maxima*1.1:
                    ""
                    # Lectura copiada de l'anterior per haver fet una sobreestimació
                elif lectures_dif >= dif_maxima * 5 and not(no_consum_mensual):
                    ""
                    # Possible reclamació. La diferencia es superior a 5 cops el consum mensual
                else:
                    if not lectures_dif:
                        ""
                        # Ja està copiada
                    else:
                        # Diferencia superior a diferencia màxima
                        if not pol_read['name'] in lectures_massa_diferencia:
                            lectures_massa_diferencia.append(pol_read['name'])

        except Exception, e:
            print e
            errors.append({pol_id:e})
            print e
    return lectures_massa_diferencia

def load_new_measures_fake(O, contract_id, mtype=range(1,7)+[8], start_date=None):
    meters_id = O.GiscedataLecturesComptador.search([('polissa', '=', contract_id)])
    new_measures = []
    for meter_id in meters_id:
        try:
            invoice_measures = get_measures_by_meter(O, meter_id, range(1,12), pool=False)
            new_measures += get_measures_by_meter(O, meter_id, mtype, True, invoice_measures[0]['name'])
        except Exception, e:
            pass
    return new_measures

print 'Reading contracts ...'
contracts=get_detained()
print 'Pending contracts ', len(contracts), contracts
n=0

# Fix contracts
contracts_fixed = []
for contract_name in contracts:
    start_date = None
    end_date = None

    c = O.GiscedataPolissa.search([('name', '=', contract_name)])
    if not c:
        continue
    contract_id = c[0]
    last_measure = O.GiscedataPolissa.read(contract_id,['data_ultima_lectura'])
    quarantine = {'kWh': [], 'euro': []}

    new_measures =  load_new_measures_fake(O, contract_id)
    old_measures = get_measures_by_contract(O, contract_id, range(1,12))
    lects = []
    fields_to_read = ['name', 'comptador', 'periode', 'lectura', 'origen_id', 'observacions']
    if old_measures[0]['origen_id'][0] not in [7,10,11]:
        end_date = old_measures[0]['name']
    else:
        if new_measures:
            end_date = new_measures[-1]['name']
            for new_measure in new_measures:
                lects.append(read_measures(O, new_measure['id'], fields_to_read, True))

    out = ''
    fields_to_search = [('polissa', '=', contract_id)]
    fields_to_read = ['active', 'data_alta', 'data_baixa']
    meters = get_meters(O, fields_to_search, fields_to_read)

    tobe_fixed = 0

    if not isinstance(meters, list):
        meters = [meters]

    fields_to_search = [('comptador.polissa', '=', contract_id)]
    if start_date:
        fields_to_search.append(('name', '>=', start_date))
    if end_date:
        fields_to_search.append(('name', '<=', end_date))

    fields_to_read = ['name', 'comptador', 'periode', 'lectura', 'origen_id', 'observacions']
    lects += get_measures(O, fields_to_search, fields_to_read, pool=False, active_test=False)
    lects += remove_modmeter_lect(meters, lects)

    n_invoices = 0
    try:
        n_invoices=check_contract(O, contract_id, lects)
    except Exception ,e:
        continue
    if n_invoices > invoices_max:
        continue

    if n==contracts_max:
        break
    print '#### %s;%s;%d;%s' % (contract_id,contract_name,n_invoices ,last_measure['data_ultima_lectura'])
    contracts_fixed.append(contract_id)

    n+=1
    quarantine = {'kWh': [], 'euro': []}

    old_measures = get_measures_by_contract(O, contract_id, range(1,12))
    new_measures = load_new_measures(O, contract_id)
    if old_measures[0]['origen_id'][0] not in [7,10,11]:
        end_date = old_measures[0]['name']
    else:
        if new_measures:
            end_date = new_measures[-1]['name']
    o = None
    try:
        o = fix_contract(O, contract_id, quarantine, start_date, end_date)
    except Exception as e:
        print 'failed fixing contract %d' % contract_id
        continue
    if o:
        out += o
    adelantar_polissa_endarerida([contract_id])

contract_remove_invoices = []
# Remove failing issues
print "Remove Failing issues. Eliminem les factures de les polisses seguents:"
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
for contract_id in contracts_fixed:
    search_pattern = [('polissa_id', '=', contract_id),
                      ('type', 'in', ['out_invoice','out_refund']),
                      ('invoice_id.state', '=', 'draft'),
                      ('invoice_id.date_invoice', '>', yesterday),
                      ]
    invoices_ids = get_invoices(O, search_pattern, None, False)
    invoices = read_invoices(O, invoices_ids, [])
    valid = [True if ((invoice['amount_total']/invoice['dies']) < euro_perday_max) 
                    and((invoice['energia_kwh']/invoice['dies']) < kwh_perday_max) 
            else False 
            for invoice in invoices]

    if not all(valid):
        contract_name = O.GiscedataPolissa.read(contract_id,['name'])['name']   
        contract_remove_invoices.append(contract_name)
        fact_obj.unlink(invoices_ids,{})
print contract_remove_invoices

# Deliver invoices
print "Deliver invoices. Polisses que obririem i enviariem:"
contract_deliver_invoices = []
contracts_ids = list(set(contracts_fixed))
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
for contract_id in contracts_ids:
    pagador_id = pol_obj.read(contract_id, ['pagador'])['pagador'][0]
    lang = partner_obj.read(pagador_id, ['lang'])['lang']
    search_pattern = [('polissa_id', '=', contract_id),
                      ('type', 'in', ['out_invoice','out_refund']),
                      ('invoice_id.state', '=', 'draft'),
                      ('invoice_id.date_invoice', '>', yesterday),
                      ]
    invoices_ids = get_invoices(O, search_pattern, None, False)
    if not invoices_ids:
        continue
    contract_name = O.GiscedataPolissa.read(contract_id,['name'])['name']   
    contract_deliver_invoices.append(contract_name)
    open_and_send(O, invoices_ids, lang,
            send_refund=True,
            send_rectified=True,
            send_digest=True,
            num_contracts=1)
print contract_deliver_invoices
# vim: ts=4 sw=4 et
