#!/usr/bin/env python
# -*- coding: utf-8 -*-

from erppeek import Client
import configdb
from consolemsg import step, success, error, warn, color, printStdError
from datetime import datetime, timedelta

def main():
    def factures_dextralines_en_estat_correcte():
        all_el = el_obj.search([('product_id','=',fracc_prod_id),
                                ('active','=',True),
                                ('total_amount_pending','>',0)
                                ])
        for el in all_el:
            extra_line = el_obj.browse(el)
            factura_origin_id = int(extra_line.origin)
            fact = fact_obj.browse(factura_origin_id)
            ps = fact.invoice_id.pending_state
            if ps and ps.id in [correct_state_dp, correct_state_bs]:
                if ps.process_id.id == 1:
                    ai_obj.set_pending( [fact.invoice_id.id], estat_fracc_extra_dp)
                else:
                    ai_obj.set_pending( [fact.invoice_id.id], estat_fracc_extra_bs)
            else:
                if fact.invoice_id.pending_state:
                    print("La factura {} no té estat correcte.Té estat: {}".format(fact.number, fact.invoice_id.pending_state.name))
                else:
                    print("La factura {} no té estat correcte.Té estat: False".format(fact.number))

    def extralines_factures_liquidades():
        day_to_compare = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        all_paid_el = el_obj.search([('product_id','=',fracc_prod_id),
                            ('active','=',True),
                            ('total_amount_pending','=',0),
                            ('write_date','>=', day_to_compare)
                            ])
        for el in all_paid_el:
            extra_line = el_obj.browse(el)
            factura_origin_id = int(extra_line.origin)
            fact = fact_obj.browse(factura_origin_id)
            ps = fact.invoice_id.pending_state
            if ps and ps.id in [estat_fracc_extra_dp, estat_fracc_extra_bs]:
                if ps.process_id.id == 1:
                    ai_obj.set_pending( [fact.invoice_id.id], correct_state_dp)
                else:
                    ai_obj.set_pending( [fact.invoice_id.id], correct_state_bs)
            else:
                if fact.invoice_id.pending_state:
                    print("La factura {} no té estat fraccionament.Té estat: {}".format(fact.number, fact.invoice_id.pending_state.name))
                else:
                    print("La factura {} no té estat fraccionament.Té estat: False".format(fact.number))


    step("Connectant a l'erp")
    c = Client(**configdb.erppeek)
    success("Connectat a: {}".format(c))
    success("Usuaria: {}".format(c.user))

    ai_obj = c.model('account.invoice')
    aips_obj = c.model('account.invoice.pending.state')
    fact_obj = c.model('giscedata.facturacio.factura')
    el_obj = c.model('giscedata.facturacio.extra')
    product_obj = c.model('product.product')

    fracc_prod_id = product_obj.search([('name','=','Pagament Fraccionat')])
    estat_fracc_extra_dp = aips_obj.search([('process_id','=',1), ('name','ilike','fraccionament extralines')])[0]
    estat_fracc_extra_bs = aips_obj.search([('process_id','=',3), ('name','ilike','fraccionament extralines')])[0]

    correct_state_dp = aips_obj.search([('process_id','=',1),('name','ilike','correct')])[0]
    correct_state_bs = aips_obj.search([('process_id','=',3),('name','ilike','correct')])[0]

    step("Actualitzant factures d'extralines en estat correcte...")
    factures_dextralines_en_estat_correcte()
    step("Actualitzant factures d'extralines en estat correcte...")
    extralines_factures_liquidades()

if __name__=='__main__':
    success("Iniciant procés d'actualització de factures amb extralines de fraccionaments...")
    res = main()
    success("Procés finalitzat")

# vim: et ts=4 sw=4