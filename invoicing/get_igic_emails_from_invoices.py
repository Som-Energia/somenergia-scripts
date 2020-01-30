#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from erppeek import Client
import configdb
from consolemsg import step, success, error, warn

step("Connectant a l'erp")
O = Client(**configdb.erppeek)
success("Connectat")

obj_fact = O.GiscedataFacturacioFactura
obj_pol = O.GiscedataPolissa
obj_add = O.ResPartnerAddress


def search_igic_ids():
	ids_a = obj_fact.search([('date_invoice','>=','2020-01-01'),('cups_id.name','like','ES00316%')])
	ids_b = obj_fact.search([('date_invoice','>=','2020-01-01'),('cups_id.name','like','ES0401%')])
	return ids_a + ids_b

def get_invoices_emails(ids):

	fact_data = obj_fact.read(ids,['address_invoice_id','polissa_id'])
	f_address_ids = [data['address_invoice_id'][0] for data in fact_data]

	polisses_ids = [data['polissa_id'][0] for data in fact_data] 
	pol_data = obj_pol.read(polisses_ids,['direccio_notificacio'])
	p_address_ids = [data['direccio_notificacio'][0] for data in pol_data]

	address_mails = obj_add.read(list(set(f_address_ids+p_address_ids)),['email'])
	emails = [address_mail['email'] for address_mail in address_mails]

	return list(set(emails))

def output_emails(emails):
	for email in emails:
		print email	

if __name__=='__main__':
	ids = search_igic_ids()
	step("Factures trobades {}",len(ids))
	emails = get_invoices_emails(ids)
	step("Mails unics {}",len(emails))
	output_emails(emails)

# vim: et ts=4 sw=4