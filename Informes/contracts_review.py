#!/usr/bin/env python
# -*- coding: utf-8 -*-

import erppeek
import dbconfig
import csv
import codecs
import datetime
from yamlns import namespace as ns

contract_header = {
        'ca_ES': ['CIF','Titular','Adreça','CUPS','Data Alta','Data Baixa','Contracte',
            'Distribuidora','Tarifa','Potència contractada P1 (kW)','Potència contractada P2 (kW)',
            'Potència contractada P3 (kW)','Lloguer'],
        'es_ES': ['CIF','Titular','Dirección','CUPS','Fecha Alta','Fecha Baja','Contrato',
            'Distribuidora','Tarifa','Potencia contratada P1 (kW)','Potencia contratada P2',
            'Potencia contratada P3','Alquiler']
        }

billc_header = {
        'ca_ES': ['CIF' ,'Titular', 'Adreça', 'CUPS', 'Contracte'],
        'es_ES': ['CIF' ,'Titular', 'Dirección', 'CUPS', 'Contrato'],
        }

bill_header = {
        'ca_ES': ['Número','Data inici','Data final','Tipus','Total Potència (€)','Total Energia (€)',
            'Total Reactiva (€)','Total Lloguer (€)','Total sense IVA (€)','Total (€)',
            'Total Energia P1 (€)', 'Total Energia P2 (€)','Total Energia P3 (€)',
            'Total Potència P1 (€)', 'Total Potència P2 (€)','Total Potència P3 (€)',
            'Preu Energia P1 (€/kWh)', 'Preu Energia P2 (€/kWh)','Preu Energia P3 (€/kWh)',
            'Preu Potència P1 (€/kW)', 'Preu Potència P2 (€/kW)','Preu Potència P3 (€/kW)'],
        'es_ES': ['Número','Fecha inicio','Fecha final','Tipo','Total Potencia (€)','Total Energia (€)',
            'Total Reactiva (€)','Total Alquiler (€)','Total sin IVA (€)','Total (€)',
            'Total Energia P1 (€)', 'Total Energia P2 (€)','Total Energia P3 (€)',
            'Total Potencia P1 (€)', 'Total Potencia P2 (€)','Total Potencia P3 (€)',
            'Preu Energia P1 (€/kWh)', 'Preu Energia P2 (€/kWh)','Preu Energia P3 (€/kWh)',
            'Preu Potencia P1 (€/kW)', 'Preu Potencia P2 (€/kW)','Preu Potencia P3 (€/kW)']
        }

bill_prefix = {
        'ca_ES': ['Energia activa consumida ' ,'Energia reactiva consumida ' ,'Maxímetre ', 'Excés '],
        'es_ES': ['Energía activa consumida ' ,'Energia reactiva consumida ' ,'Maxímetro ', 'Exceso '],
        }

client = erppeek.Client(**dbconfig.erppeek)
contract_obj = client.model('giscedata.polissa')
contract_power_obj = client.model('giscedata.polissa.potencia.contractada.periode')
partner_obj = client.model('res.partner')
cups_obj = client.model('giscedata.cups.ps')
meter_obj = client.model('giscedata.lectures.comptador')
bill_obj = client.model('giscedata.facturacio.factura')
bill_line_obj = client.model('giscedata.facturacio.factura.linia')
energy_line_obj = client.model('giscedata.facturacio.lectures.energia')
power_line_obj = client.model('giscedata.facturacio.lectures.potencia')
invoice_obj = client.model('account.invoice')
invoice_line_obj = client.model('account.invoice.line')

def get_period(string, start='(', stop=')'):
    return string[string.index(start)+1:string.index(stop)]

def dump_contracts(contracts, filename, lang):
    fields = ['cif','titular','adreca','cups','data_alta','data_baixa','name',
            'distribuidora','tarifa','P1','P2','P3','lloguer']

    with codecs.open(filename, 'wb', 'utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',
                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(contract_header[lang])
        for contract in contracts:
            row = [contract.get(field)
                    for field in fields]
            writer.writerow(row)

def date_in(d,s,e):
    d = datetime.datetime.strptime(d,'%Y-%m-%d').date()
    return d >= s and d < e

def dump_bills(contracts, start, end, filename, lang):
    start = datetime.datetime.strptime(start,'%Y-%m-%d').date()
    end = datetime.datetime.strptime(end,'%Y-%m-%d').date()

    contract_fields = ['vat','titular','adreca','cups','name']
    bill_fields = ['number','data_inici','data_final','type',
            'total_potencia','total_energia','total_reactiva','total_lloguers',
            'amount_untaxed','amount_total',
            'P1 energia price','P2 energia price','P3 energia price',
            'P1 potencia price','P2 potencia price','P3 potencia price',
            'P1 energia price unit','P2 energia price unit','P3 energia price unit',
            'P1 potencia price unit','P2 potencia price unit','P3 potencia price unit']


    period_fields = ['P1','P2','P3','P4','P5','P6']

    header = billc_header[lang] + \
              bill_header[lang] + \
              [bill_prefix[lang][0] + period for period in period_fields] + \
              [bill_prefix[lang][1] + period for period in period_fields] + \
              [bill_prefix[lang][2] + period for period in period_fields] + \
              [bill_prefix[lang][3] + period for period in period_fields]

    with codecs.open(filename, 'wb',' utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';',
                quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        
        for contract in contracts:
            search_params = [('polissa_id','=', contract['id']),
                    ('invoice_id.type','in', ['out_invoice','out_refund'])]
            bills_id = bill_obj.search(search_params)
            for bill_id in bills_id:
                bill = get_bill(bill_id)
                if not date_in(bill['date_invoice'],start,end):
                    continue
                row = [contract.get(field)
                        for field in contract_fields]
                row += [bill.get(field)
                        for field in bill_fields]
    
                row += [bill['energia_activa'].get(field)
                        for field in period_fields]
                
                row += [bill['energia_reactiva'].get(field)
                        for field in period_fields]
    
                row += [bill['maximetre'].get(field)
                        for field in period_fields]
    
                row += [bill['exces'].get(field)
                        for field in period_fields]
                writer.writerow(row)

def get_contract(contract_id):
    fields = ['name','titular','vat','cups','distribuidora','data_baixa','data_alta','tarifa']
    contract = contract_obj.read(contract_id, fields)

    contract['vat'] = partner_obj.read(contract['titular'][0], ['vat'])['vat'][2:]
    contract['titular'] = contract['titular'][1]
    contract['adreca'] = cups_obj.read(contract['cups'][0], ['direccio'])['direccio'].replace(';',',')
    contract['cups'] = contract['cups'][1]
    contract['distribuidora'] = contract['distribuidora'][1]
    contract['tarifa'] = contract['tarifa'][1]

    search_params = [('polissa_id', '=', contract_id)]
    periods_id = contract_power_obj.search(search_params)
    fields = ['periode_id','potencia']


    contract.update({
            get_period(period['periode_id'][1]):period['potencia']
            for period in contract_power_obj.read(periods_id,fields)})

    search_params = [('polissa','=',contract_id)]
    meter_id = meter_obj.search(search_params)[0]
    contract['lloguer'] = 'Si' if meter_obj.read(meter_id, ['lloguer'])['lloguer'] else 'No'
    return contract 

def get_energy(bill_id):
    energy_lines_id = energy_line_obj.search([('factura_id','=',bill_id)])
    energy_lines = energy_line_obj.read(energy_lines_id, ['name','consum','tipus'])
    energy = {'activa':{}, 'reactiva':{}}
    for line in energy_lines:
        period = get_period(line['name'])
        consum = line['consum']
        tipus = line['tipus']
        if period not in energy:
            energy[tipus].setdefault(period, consum)
        else:
            energy[tipus][period] += consum
    return energy

def get_power(bill_id):
    power_lines_id = power_line_obj.search([('factura_id','=',bill_id)])
    power_lines = power_line_obj.read(power_lines_id, ['name','pot_maximetre','exces'])
    maximetre = {}
    exces = {}
    if power_lines:
        for line in power_lines:
            period = line['name']
            maximetre_ = line['pot_maximetre']
            exces_ = line['exces']
            if period not in maximetre:
                maximetre.setdefault(period, maximetre_)
                exces.setdefault(period, exces_)
            else:
                maximetre[period] = max(maximetre[period],maximetre_)
                exces[period] += exces_
    return maximetre,exces 

def get_bill(bill_id):
    fields = ['invoice_id','data_inici','data_final',
            'total_energia','total_potencia','total_lloguers','total_reactiva']
    bill = bill_obj.read(bill_id, fields)

    fields = ['number','amount_untaxed','amounth_tax','amount_total','type','date_invoice']
    invoice = invoice_obj.read(bill['invoice_id'][0], fields)
    bill.update({
        'number': invoice['number'],
        'amount_untaxed': invoice['amount_untaxed'],
        'amount_tax': invoice['amount_untaxed'],
        'amount_total': invoice['amount_total'],
        'type': invoice['type'],
        'date_invoice': invoice['date_invoice']})

    bill_lines_id = bill_line_obj.search([('factura_id','=',bill_id)])
    fields = ['tipus','name','price_subtotal','quantity', 'price_unit_multi']
    bill_lines = bill_line_obj.read(bill_lines_id, fields)

    bill.update({
        '%s %s price' % (line['name'],line['tipus']): line['price_subtotal']
        for line in bill_lines
        })
    bill.update({
        '%s %s price unit' % (line['name'],line['tipus']): line['price_unit_multi']
        for line in bill_lines
        })

    energy_lines = get_energy(bill_id)
    maximetre_lines,exces_lines = get_power(bill_id)

    bill.update({
        'energia_activa': energy_lines['activa'],
        'energia_reactiva': energy_lines['reactiva'],
        'maximetre': maximetre_lines,
        'exces': exces_lines
        })
    return bill 

def build(start, end, partner, contractsfile, billsfile,
        lang='es_ES', **args):

    partner_id = partner_obj.search([('ref','=',partner)])[0]
    search_params = [('titular','=',partner_id),('state','=','activa')]
    contracts_id = contract_obj.search(search_params)
    contracts = [get_contract(contract_id) for contract_id in contracts_id]
    dump_contracts(contracts, contractsfile, lang)
    dump_bills(contracts, start, end, billsfile, lang)

def parseArguments():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest="subcommand",
        )
    build = subparsers.add_parser('build',
        help="Build monthly report")
    for sub in build,: 
        sub.add_argument(
            'start',
            type=str,
            help="Start date (isoformat)",
            )
        sub.add_argument(
            'end',
            type=str,
            help="End date (isoformat)",
            )
        sub.add_argument(
            'partner',
            type=str,
            help="Partner",
            )
        sub.add_argument(
            'contractsfile', 
            type=str,
            help="Output contracts file",
            )
        sub.add_argument(
            'billsfile', 
            type=str,
            help="Output bills file",
            )
        sub.add_argument(
            '--lang', '-l',
            type=str,
            help="Language",
            )
    return parser.parse_args(namespace=ns())

def main():
    args = parseArguments()
    print ns(args).dump()
    print args
    globals()[args.subcommand](**args)

if __name__ == '__main__':
    main()


# vim: et ts=4 sw=4
