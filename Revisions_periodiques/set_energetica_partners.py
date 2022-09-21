#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from erppeek import Client
import configdb
from consolemsg import step, success, error, warn
from tqdm import tqdm
import sys

ENERGETICA_PARTNER_ID = 38039
ENERGETICA_PARTNER_CATEGORY_ID = 24

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

doit = 'si' in sys.argv or '--doit' in sys.argv
query = '--query' in sys.argv
success('')
if doit:
    success("Es faran canvis als partners (doit=True)")
else:
    success("No es faran canvis als partners (doit=False)")

#Objectes
pol_obj = O.GiscedataPolissa
par_obj = O.ResPartner
cat_obj = O.ResPartnerCategory

def get_partner_category_name(partner_category_id):
    return cat_obj.read(partner_category_id, ['name'])['name']

def search_agreement_partner_contract_uncategorized_partners(partner_id, partner_category_id):
    step("Cercant polisses d'energetica...")
    pol_ids = pol_obj.search([('soci', '=', partner_id)], context={'active_test':False})
    partners = set()
    step('{} pòlisses trobades', len(pol_ids))

    for pol_id in tqdm(pol_ids):
        pol = pol_obj.browse(pol_id)

        if (pol.titular and
            pol.titular.id not in partners and
            partner_category_id not in set(pol.titular.category_id.id)):
            partners.add(pol.titular.id)

        if (pol.pagador and
            pol.pagador.id not in partners and
            partner_category_id not in set(pol.pagador.category_id.id)):
            partners.add(pol.pagador.id)

        if (pol.direccio_pagament and
            pol.direccio_pagament.partner_id and
            pol.direccio_pagament.partner_id.id not in partners and
            partner_category_id not in set(pol.direccio_pagament.partner_id.category_id.id)):
            partners.add(pol.direccio_pagament.partner_id.id)

        if (pol.direccio_notificacio and
            pol.direccio_notificacio.partner_id and
            pol.direccio_notificacio.partner_id.id not in partners and
            partner_category_id not in set(pol.direccio_notificacio.partner_id.category_id.id)):
            partners.add(pol.direccio_notificacio.partner_id.id)

    step('{} clients sense categoria {} trobats', len(partners), get_partner_category_name(partner_category_id))
    return list(partners)

def set_agreement_partner_partners_category(partner_ids, partner_category_id):
    step('Afegint categoria {} a {} clients ', get_partner_category_name(partner_category_id), len(partner_ids))
    if doit:
        par_obj.write(partner_ids, {'category_id': [(4, partner_category_id)]})
        warn("modificats")
    else:
        warn("no modificats (activar amb --doit)")

def show_partners(partner_ids):
    step(" ID     DNI/NIF      CODI    NOM")
    for partner_id in partner_ids:
        par = par_obj.browse(partner_id)
        step("{:7} {:12} {:7} {}", par.id, par.vat, par.ref, par.name)

def search_energetica_contract_uncategorized_partners():
    return search_agreement_partner_contract_uncategorized_partners(ENERGETICA_PARTNER_ID, ENERGETICA_PARTNER_CATEGORY_ID)

def set_energetica_partners_category(partner_ids):
    set_agreement_partner_partners_category(partner_ids, ENERGETICA_PARTNER_CATEGORY_ID)

def show_energetica_partners(partner_ids):
    success("Clients d'energetica sense categoria:")
    show_partners(partner_ids)

if __name__=='__main__':
    partner_ids = search_energetica_contract_uncategorized_partners()
    show_energetica_partners(partner_ids)
    set_energetica_partners_category(partner_ids)
    success("Fi.")


# vim: et ts=4 sw=4
