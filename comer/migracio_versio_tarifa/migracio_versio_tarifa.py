#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from erppeek import Client
import argparse
import configdb
from datetime import datetime, timedelta
from yamlns import namespace as ns

def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        '--desti',
        dest='erp_desti',
        help="URL del servidor ERP de destí"
    )

    parser.add_argument(
        '--tarifa',
        dest='nom_tarifa',
        help="Nom de la tarifa que s'ha de còpiar"
    )

    args = parser.parse_args(namespace=ns())

    return args

def ssl_unverified_context():
    import ssl

    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

def search_tariff_id(c, name):
    tarifa_o = c.model('product.pricelist')
    tarifa_id = tarifa_o.search([('name', '=', name)])[0]
    return tarifa_id

def serialitzar_item(cpre, cprod, item_id):
    data = {}

    item_o = cprod.model('product.pricelist.item')
    tarifa_pre_o = cpre.model('product.pricelist')
    tarifa_prod_o = cprod.model('product.pricelist')

    item_bw = item_o.browse(item_id)

    params = [
        'base', 'base_price', 'base_pricelist_id', 'categ_id',
        'min_quantity', 'name', 'price_discount', 'price_max_margin',
        'price_min_margin', 'price_round', 'price_subcharge',
        'price_version_id', 'product_category_id', 'product_id',
        'product_tmpl_id', 'sequence', 'tram', 'tram_quantity'
    ]

    data = item_o.read(item_id, params)

    data['product_tmpl_id'] = data['product_tmpl_id'][0] if data['product_tmpl_id'] else False
    data['categ_id'] = data['categ_id'][0] if data['categ_id'] else False
    data['base_pricelist_id'] = data['base_pricelist_id'][0] if data['base_pricelist_id'] else False

    if data.get('base_pricelist_id'):
        name_tarifa_prod = tarifa_prod_o.read(data['base_pricelist_id'], ['name'])['name']
        data['base_pricelist_id'] = tarifa_pre_o.search([('name', '=', name_tarifa_prod)])[0]

    data['price_version_id'] = data['price_version_id'][0] if data['price_version_id'] else False
    data['product_category_id'] = data['product_category_id'][0] if data['product_category_id'] else False
    data['product_id'] = data['product_id'][0] if data['product_id'] else False
    data.pop('id')

    return [0, 0, data]

def serialitzar_dades_version_prod(cpre, cprod, version_id, tarifa_id):
    data = {}

    version_o = cprod.model('product.pricelist.version')

    version_bw = version_o.browse(version_id)

    items = []
    for item_id in version_bw.items_id:
        item = serialitzar_item(cpre, cprod, item_id.id)
        items.append(item)

    data['name'] = version_bw.name
    data['active'] = version_bw.active
    data['pricelist_id'] = tarifa_id
    data['date_end'] = version_bw.date_end
    data['date_start'] = version_bw.date_start
    data['items_id'] = items

    return data

def search_last_version_id(c, tarifa_id):
    version_o = c.model('product.pricelist.version')

    search_params = [
        ('pricelist_id', '=', tarifa_id),
        ('date_end', '=', False)
    ]
    version_ids = version_o.search(search_params, context={'active_test': False})
    version_id = sorted(version_ids)[-1]

    return version_id

def create_version_tariff(c, data):
    version_o = c.model('product.pricelist.version')
    version_o.create(data)

def set_version_last_date(c, version_id, date):
    version_o = c.model('product.pricelist.version')
    date_end = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    version_o.write(version_id, {'date_end': date_end})

def migracio(args):
    ssl_unverified_context()
    import pudb; pu.db

    if args.erp_desti == 'testing':
        erppeek_desti = configdb.erppeek_test
    elif args.erp_desti == 'staging':
        erppeek_desti = configdb.erppeek_stage
    elif args.erp_desti == 'pre':
        erppeek_desti = configdb.erppeek_pre
    elif args.erp_desti == 'pro':
        erppeek_desti = configdb.erppeek_pro
    else:
        print "No s'ha trobat servidor de destí"
        return

    cpre = Client(**erppeek_desti)
    cprod = Client(**configdb.erppeek_prod)

    tarifa = args.nom_tarifa

    tarifa_pre_id = search_tariff_id(cpre, tarifa)
    tarifa_prod_id = search_tariff_id(cprod, tarifa)

    # Busquem la última versió de la tarifa
    version_prod_id = search_last_version_id(cprod, tarifa_prod_id)

    data = serialitzar_dades_version_prod(cpre, cprod, version_prod_id, tarifa_pre_id)

    version_pre_id = search_last_version_id(cpre, tarifa_pre_id)
    set_version_last_date(cpre, version_pre_id, data['date_start'])

    if data:
        create_version_tariff(cpre, data)
        print "Migració de tarifa completada amb èxit!"

if __name__ == "__main__":
    args = parse_arguments()
    migracio(args)

